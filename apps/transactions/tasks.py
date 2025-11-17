import logging
from decimal import Decimal

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.dealerships.models import Dealership, DealershipAction, DealershipCarInventory
from apps.users.models import CustomerProfile

from .models import Offer
from .models import Transaction as TransactionModel

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_pending_offers(self):
    """
    Processing all pending offers from buyers.
    Called every 5 minutes.
    """
    logger.info("Starting pending offers processing")

    pending_offers = Offer.objects.filter(status="PENDING", is_active=True).select_related(
        "customer", "car_model", "dealership_match"
    )

    results = {"processed": 0, "matched": 0, "rejected": 0, "completed": 0, "errors": 0}

    for offer in pending_offers:
        try:
            result = process_single_offer(offer)
            results["processed"] += 1
            results[result] += 1

            logger.info(f"Offer {offer.id}: {result}")
        except Exception as e:
            results["errors"] += 1
            logger.error(f"Error processing offer {offer.id}: {str(e)}")

    logger.info(f"Offers processing completed: {results}")
    return results


def process_single_offer(offer):
    """
    Processing a single offer.

    Logic:
    1. Search for suitable dealerships (if cars are in stock)
    2. Calculate the final price taking into account dealership promotions
    3. Check if the price is acceptable to the buyer
    4. If yes, match; if not, reject
    """
    suitable_dealerships = find_suitable_dealerships(offer)

    if not suitable_dealerships:
        offer.status = "REJECTED"
        offer.save(update_fields=["status"])
        return "rejected"

    best_match = select_best_dealership(offer, suitable_dealerships)

    if not best_match:
        offer.status = "REJECTED"
        offer.save(update_fields=["status"])
        return "rejected"

    if best_match["final_price"] <= offer.max_price:
        offer.status = "MATCHED"
        offer.dealership_match = best_match["dealership"]
        offer.save(update_fields=["status", "dealership_match"])

        if complete_sale(offer, best_match):
            return "completed"
        else:
            return "matched"
    else:
        offer.status = "REJECTED"
        offer.save(update_fields=["status"])
        return "rejected"


def find_suitable_dealerships(offer):
    """Find dealerships that have desired model in stock."""
    return DealershipCarInventory.objects.filter(
        car_model=offer.car_model, count__gt=0, is_active=True, dealership__is_active=True
    ).select_related("dealership", "car_model")


def select_best_dealership(offer, suitable_inventories):
    """
    Selecting the best salon based on:
    - Average purchase price + 30% markup
    - Active salon promotions
    """
    now = timezone.now()
    best_match = None
    best_price = Decimal("999999.99")

    for inventory in suitable_inventories:
        dealership = inventory.dealership

        base_price = inventory.purchase_price_avg * Decimal("1.30")

        active_actions = DealershipAction.objects.filter(
            dealership=dealership, car_models=offer.car_model, is_active=True, start_date__lte=now, end_date__gte=now
        )

        final_price = base_price

        if active_actions.exists():
            max_discount = active_actions.aggregate(max_discount=Max("discount_percentage"))["max_discount"]

            if max_discount:
                discount_amount = base_price * (max_discount / 100)
                final_price = base_price - discount_amount

        if final_price < best_price:
            best_price = final_price
            best_match = {
                "dealership": dealership,
                "inventory": inventory,
                "base_price": base_price,
                "final_price": final_price,
            }
    return best_match


@transaction.atomic
def complete_sale(offer, match_data):
    """
    Completing the transaction.

    1. Checking the buyer's balance
    2. Debiting the buyer
    3. Crediting the salon
    4. Decreasing the salon's inventory
    5. Creating the transaction
    6. Updating the offer status
    """
    try:
        customer = offer.customer
        dealership = match_data["dealership"]
        inventory = match_data["inventory"]
        final_price = match_data["final_price"]

        if customer.balance < final_price:
            logger.warning(f"Insufficient balance for customer {customer.id}")
            return False

        customer.balance -= final_price
        customer.save(update_fields=["balance"])

        dealership.balance += final_price
        dealership.save(update_fields=["balance"])

        inventory.count -= 1
        inventory.save(update_fields=["count"])

        dealership_ct = ContentType.objects.get_for_model(Dealership)
        customer_ct = ContentType.objects.get_for_model(CustomerProfile)

        TransactionModel.objects.create(
            transaction_type="SALE",
            amount=final_price,
            car_model=offer.car_model,
            count=1,
            sender_content_type=dealership_ct,
            sender_object_id=dealership.id,
            recipient_content_type=customer_ct,
            recipient_object_id=customer.id,
        )

        offer.status = "BOUGHT"
        offer.save(update_fields=["status"])

        logger.info(
            f"Sale completed: Customer {customer.id} bought "
            f"{offer.car_model.name} from {dealership.name} for {final_price}"
        )
        return True

    except Exception as e:
        logger.error(f"Error completing sale: {str(e)}")
        raise


@shared_task(bind=True)
def cleanup_expired_offers(self):
    """
    Clearing old offers.
    Offers older than 30 days are marked as REJECTED.
    """
    logger.info("Starting expired offers cleanup")

    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    expired_offers = Offer.objects.filter(status="PENDING", created_at__lt=thirty_days_ago, is_active=True)

    count = expired_offers.count()
    expired_offers.update(status="REJECTED", is_active=False)

    logger.info(f"Cleaned up {count} expired offers")

    return {"cleaned": count}


@shared_task(bind=True)
def process_specific_offer(self, offer_id):
    """
    Processing a specific offer.
    """
    try:
        offer = Offer.objects.get(id=offer_id, status="PENDING")
        result = process_single_offer(offer)
        logger.info(f"Manual offer processing: {offer_id} - {result}")
        return {"offer_id": offer_id, "result": result}
    except Offer.DoesNotExist:
        logger.error(f"Offer {offer_id} not found or not pending")
        return {"error": "Offer not found"}
    except Exception as e:
        logger.error(f"Error processing offer {offer_id}: {str(e)}")
        raise
