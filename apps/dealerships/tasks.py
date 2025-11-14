import logging
from decimal import Decimal

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Avg, Max, Sum
from django.utils import timezone

from apps.suppliers.models import Supplier, SupplierAction, SupplierCarOffer
from apps.transactions.models import Transaction
from apps.vehicles.models import CarModel

from .models import Dealership, DealershipCarInventory, DealershipPreferredSupplier

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_dealership_purchases(self):
    """
    Processing purchases for every dealership
    Called every 10 minutes
    """
    logger.info("Starting dealership purchases processing")

    active_dealerships = Dealership.objects.filter(is_active=True)

    results = {"processed": 0, "purchased": 0, "skipped": 0, "errors": 0}

    for dealership in active_dealerships:
        try:
            purchased = process_single_dealership_purchase(dealership)
            results["processed"] += 1
            results["purchased"] += purchased

            logger.info(f"Dealership {dealership.name}: purchased {purchased} cars")
        except Exception as e:
            results["errors"] += 1
            logger.error(f"Error processing dealership {dealership.id}: {str(e)}")

    logger.info(f"Purchases completed: {results}")
    return results


def process_single_dealership_purchase(dealership):
    """
    Processing purchases for every dealership.

    Logic:
    1. Analyze demand based on sales history
    2. Identify purchasing patterns
    3. Find the best deals, taking into account promotions
    4. Check balance
    5. Complete purchase
    """
    purchased_count = 0

    demand_analysis = analyze_dealership_demand(dealership)

    if not demand_analysis:
        logger.info(f"No demand data for dealership {dealership.name}")
        return 0

    for model_data in demand_analysis[:5]:
        car_model = model_data["car_model"]
        recommended_quantity = model_data["recommended_quantity"]

        best_offer = find_best_supplier_offer(car_model, dealership)

        if not best_offer:
            logger.info(f"No offers found for {car_model.name}")
            continue

        total_cost = best_offer["final_price"] * recommended_quantity

        if dealership.balance < total_cost:
            recommended_quantity = int(dealership.balance / best_offer["final_price"])

            if recommended_quantity < 1:
                logger.info(f"Insufficient balance for {dealership.name}")
                continue

            total_cost = best_offer["final_price"] * recommended_quantity

        success = execute_purchase(
            dealership=dealership,
            supplier_offer=best_offer["offer"],
            quantity=recommended_quantity,
            price_per_unit=best_offer["final_price"],
            total_cost=total_cost,
        )

        if success:
            purchased_count += recommended_quantity

    return purchased_count


def analyze_dealership_demand(dealership):
    """
    Demand analysis based on:
    - Sales history (last 30 days)
    - Current inventory
    - Preferred salon characteristics
    """
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    dealership_ct = ContentType.objects.get_for_model(Dealership)

    sales_analysis = (
        Transaction.objects.filter(
            sender_content_type=dealership_ct,
            sender_object_id=dealership.id,
            transaction_type="SALE",
            created_at__gte=thirty_days_ago,
        )
        .values("car_model")
        .annotate(total_sold=Sum("count"), avg_price=Avg("amount"))
        .order_by("-total_sold")
    )

    demand_data = []

    for sale in sales_analysis:
        car_model = CarModel.objects.get(id=sale["car_model"])

        try:
            inventory = DealershipCarInventory.objects.get(dealership=dealership, car_model=car_model)
            current_stock = inventory.count
        except DealershipCarInventory.DoesNotExist:
            current_stock = 0

        monthly_sales = sale["total_sold"]
        recommended = max(1, int(monthly_sales / 3) - current_stock)

        matches_preferences = check_model_preferences(dealership, car_model)

        if recommended > 0 and matches_preferences:
            demand_data.append(
                {
                    "car_model": car_model,
                    "monthly_sales": monthly_sales,
                    "current_stock": current_stock,
                    "recommended_quantity": recommended,
                    "priority": monthly_sales,
                }
            )

    if not demand_data and dealership.preferred_specs.exists():
        preferred_models = CarModel.objects.filter(base_specs__in=dealership.preferred_specs.all())[:3]

        for car_model in preferred_models:
            demand_data.append(
                {
                    "car_model": car_model,
                    "monthly_sales": 0,
                    "current_stock": 0,
                    "recommended_quantity": 2,
                    "priority": 1,
                }
            )

    return sorted(demand_data, key=lambda x: x["priority"], reverse=True)


def check_model_preferences(dealership, car_model):
    """Checking the model's compliance with the salon's preferences."""
    if not dealership.preferred_specs.exists():
        return True
    return dealership.preferred_specs.filter(id=car_model.base_specs.id).exists()


def find_best_supplier_offer(car_model, dealership):
    """
    Find the best offer from suppliers, taking into account promotions.
    Returns a dictionary with the offer and the final price (including discounts).
    """
    now = timezone.now()

    offers = SupplierCarOffer.objects.filter(car_model=car_model, is_active=True, stock_count__gt=0).select_related(
        "supplier"
    )

    if not offers.exists():
        return None

    best_offer = None
    best_price = Decimal("999999.99")

    for offer in offers:
        price = offer.price

        active_actions = SupplierAction.objects.filter(
            supplier=offer.supplier, is_active=True, start_date__lte=now, end_date__gte=now
        )

        if active_actions.exists():
            max_discount = active_actions.aggregate(max_discount=Max("discount_percentage"))["max_discount"]

            if max_discount:
                discount_amount = price * (max_discount / 100)
                price = price - discount_amount

        if price < best_price:
            best_price = price
            best_offer = {
                "offer": offer,
                "original_price": offer.price,
                "final_price": price,
                "discount_applied": offer.price - price,
            }

    return best_offer


@transaction.atomic
def execute_purchase(dealership, supplier_offer, quantity, price_per_unit, total_cost):
    """
    Purchase cars from a supplier.

    1. Check balance and inventory
    2. Write off funds from the dealership
    3. Decrease stock at the supplier
    4. Add to dealership inventory
    5. Create transaction
    """
    try:
        if dealership.balance < total_cost:
            logger.warning(f"Insufficient balance for dealership {dealership.id}")
            return False

        if supplier_offer.stock_count < quantity:
            quantity = supplier_offer.stock_count
            total_cost = price_per_unit * quantity

        if quantity < 1:
            return False

        dealership.balance -= total_cost
        dealership.save(update_fields=["balance"])

        supplier_offer.stock_count -= quantity
        supplier_offer.save(update_fields=["stock_count"])

        inventory, created = DealershipCarInventory.objects.get_or_create(
            dealership=dealership,
            car_model=supplier_offer.car_model,
            defaults={"count": 0, "purchase_price_avg": price_per_unit},
        )

        total_existing_value = inventory.purchase_price_avg * inventory.count
        total_new_value = price_per_unit * quantity
        new_total_count = inventory.count + quantity

        inventory.purchase_price_avg = (total_existing_value + total_new_value) / new_total_count
        inventory.count = new_total_count
        inventory.save()

        supplier_ct = ContentType.objects.get_for_model(Supplier)
        dealership_ct = ContentType.objects.get_for_model(Dealership)

        Transaction.objects.create(
            transaction_type="PURCHASE",
            amount=total_cost,
            car_model=supplier_offer.car_model,
            count=quantity,
            sender_content_type=supplier_ct,
            sender_object_id=supplier_offer.supplier.id,
            recipient_content_type=dealership_ct,
            recipient_object_id=dealership.id,
        )

        logger.info(
            f"Purchase completed: {dealership.name} bought {quantity} x "
            f"{supplier_offer.car_model.name} for {total_cost}"
        )
        return True

    except Exception as e:
        logger.error(f"Error executing purchase: {str(e)}")
        raise


@shared_task(bind=True, max_retries=3)
def update_all_preferred_suppliers(self):
    """
    Updating the list of preferred suppliers for all salons.
    Called every hour.
    """
    logger.info("Starting preferred suppliers update")

    active_dealerships = Dealership.objects.filter(is_active=True)

    results = {"processed": 0, "updated": 0, "errors": 0}

    for dealership in active_dealerships:
        try:
            updated_count = update_dealership_preferred_suppliers(dealership)
            results["processed"] += 1
            results["updated"] += updated_count

            logger.info(f"Updated {updated_count} suppliers for {dealership.name}")
        except Exception as e:
            results["errors"] += 1
            logger.error(f"Error updating suppliers for {dealership.id}: {str(e)}")

    logger.info(f"Suppliers update completed: {results}")
    return results


def update_dealership_preferred_suppliers(dealership):
    """
    Updating the list of preferred suppliers for a single salon.

    Selection criteria:
    1. Current price
    2. Active discounts
    3. Price history (trend)
    4. In stock
    """
    updated_count = 0

    relevant_models = get_relevant_models_for_dealership(dealership)

    for car_model in relevant_models:
        best_supplier = find_best_long_term_supplier(car_model, dealership)

        if best_supplier:
            preferred, created = DealershipPreferredSupplier.objects.update_or_create(
                dealership=dealership,
                car_model=car_model,
                defaults={
                    "supplier": best_supplier["supplier"],
                    "best_price": best_supplier["price"],
                },
            )
            updated_count += 1

            if created:
                logger.info(
                    f"New preferred supplier: {best_supplier['supplier'].name} "
                    f"for {car_model.name} at {dealership.name}"
                )

    return updated_count


def get_relevant_models_for_dealership(dealership):
    """Obtaining models relevant to the salon."""
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    dealership_ct = ContentType.objects.get_for_model(Dealership)

    sold_models = (
        Transaction.objects.filter(
            sender_content_type=dealership_ct,
            sender_object_id=dealership.id,
            transaction_type="SALE",
            created_at__gte=thirty_days_ago,
        )
        .values_list("car_model", flat=True)
        .distinct()
    )

    inventory_models = dealership.inventory.filter(is_active=True).values_list("car_model", flat=True)

    preferred_models = CarModel.objects.filter(base_specs__in=dealership.preferred_specs.all()).values_list(
        "id", flat=True
    )

    all_model_ids = set(list(sold_models) + list(inventory_models) + list(preferred_models))

    return CarModel.objects.filter(id__in=all_model_ids, is_active=True)


def find_best_long_term_supplier(car_model, dealership):
    """
    Finding the best supplier with a long-term perspective.

    Considered:
    - Current price
    - Frequency and size of discounts
    - Reliability (stock availability)
    """
    offers = SupplierCarOffer.objects.filter(car_model=car_model, is_active=True).select_related("supplier")

    if not offers.exists():
        return None

    best_score = -1
    best_supplier_data = None

    for offer in offers:
        score = calculate_supplier_score(offer)

        if score > best_score:
            best_score = score
            best_supplier_data = {"supplier": offer.supplier, "price": offer.price, "score": score}

    return best_supplier_data


def calculate_supplier_score(offer):
    """
    Supplier valuation calculation.

    Factors:
    - Price (40%)
    - Stock availability (30%)
    - In-stock availability (20%)
    - Cooperation history (10%)
    """
    score = 0

    competitor_offers = SupplierCarOffer.objects.filter(car_model=offer.car_model, is_active=True)

    if competitor_offers.exists():
        max_price = competitor_offers.aggregate(Max("price"))["price__max"]
        if max_price and max_price > 0:
            price_score = (1 - (offer.price / max_price)) * 40
            score += price_score

    now = timezone.now()
    active_actions = SupplierAction.objects.filter(
        supplier=offer.supplier, is_active=True, start_date__lte=now, end_date__gte=now
    )

    if active_actions.exists():
        avg_discount = active_actions.aggregate(Avg("discount_percentage"))["discount_percentage__avg"]

        if avg_discount:
            discount_score = min(avg_discount / 10, 30)
            score += discount_score

    stock_ratio = min(offer.stock_count / 10, 1.0)
    score += stock_ratio * 20

    supplier_ct = ContentType.objects.get_for_model(Supplier)
    transactions_count = Transaction.objects.filter(
        sender_content_type=supplier_ct,
        sender_object_id=offer.supplier.id,
        car_model=offer.car_model,
        transaction_type="PURCHASE",
    ).count()

    history_score = min(transactions_count / 5, 1.0) * 10
    score += history_score

    return score
