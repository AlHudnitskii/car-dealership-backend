from django.db import models
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce

from apps.dealerships.models import Dealership, DealershipAction
from apps.suppliers.models import Supplier
from apps.transactions.models import Offer, Transaction
from apps.users.models import CustomerProfile

DEALERSHIP_CT = None
CUSTOMER_CT = None
SUPPLIER_CT = None


class DealershipStatsService:
    @staticmethod
    def get_dealership_stats(dealership_id):
        """Calculates all key statistics for a single Dealership."""
        try:
            dealership = Dealership.objects.get(id=dealership_id)
        except Dealership.DoesNotExist:
            return None

        sales_data = Transaction.objects.filter(
            sender_content_type=DEALERSHIP_CT, sender_object_id=dealership_id, transaction_type="SALE"
        ).aggregate(
            total_sales_count=Coalesce(Sum("count"), 0, output_field=DecimalField()),
            total_revenue=Coalesce(Sum("amount"), 0, output_field=DecimalField()),
            unique_customers=Count("recipient_object_id", distinct=True),
        )

        purchases_data = Transaction.objects.filter(
            recipient_content_type=DEALERSHIP_CT, recipient_object_id=dealership_id, transaction_type="PURCHASE"
        ).aggregate(
            total_purchases=Coalesce(Sum("count"), 0, output_field=DecimalField()),
            total_expenses=Coalesce(Sum("amount"), 0, output_field=DecimalField()),
        )

        inventory_count = dealership.inventory.filter(is_active=True).aggregate(
            count=Coalesce(Sum("count"), 0, output_field=DecimalField())
        )["count"]

        active_promotions = DealershipAction.objects.filter(
            dealership=dealership,
            is_active=True,
            start_date__lte=models.DateTimeField(),
            end_date__gte=models.DateTimeField(),
        ).count()

        revenue = sales_data["total_revenue"]
        expenses = purchases_data["total_expenses"]

        return {
            "dealership_id": dealership.id,
            "dealership_name": dealership.name,
            "total_cars_sold": sales_data["total_sales_count"],
            "total_revenue": revenue,
            "total_purchases": purchases_data["total_purchases"],
            "total_expenses": expenses,
            "net_profit": revenue - expenses,
            "unique_customers": sales_data["unique_customers"],
            "current_inventory_count": inventory_count,
            "current_balance": dealership.balance,
            "active_promotions": active_promotions,
        }


class CustomerStatsService:
    @staticmethod
    def get_customer_stats(customer_id):
        """Calculates all key statistics for a single Customer."""

        try:
            customer = CustomerProfile.objects.get(id=customer_id)
        except CustomerProfile.DoesNotExist:
            return None

        purchases = Transaction.objects.filter(
            recipient_content_type=CUSTOMER_CT, recipient_object_id=customer_id, transaction_type="SALE"
        ).aggregate(
            total_spent=Coalesce(Sum("amount"), 0, output_field=DecimalField()),
            total_purchases=Coalesce(Sum("count"), 0, output_field=DecimalField()),
        )

        offers_data = customer.offers.aggregate(
            pending_offers=Count("id", filter=Q(status="PENDING")),
            rejected_offers=Count("id", filter=Q(status="REJECTED")),
        )

        favorite_model = (
            Transaction.objects.filter(
                recipient_content_type=CUSTOMER_CT, recipient_object_id=customer_id, transaction_type="SALE"
            )
            .values("car_model__name")
            .annotate(count=Sum("count", output_field=DecimalField()))
            .order_by("-count")
            .first()
        )

        return {
            "customer_id": customer.id,
            "customer_email": customer.user.email,
            "total_spent": purchases["total_spent"],
            "total_purchases": purchases["total_purchases"],
            "current_balance": customer.balance,
            "pending_offers": offers_data["pending_offers"],
            "rejected_offers": offers_data["rejected_offers"],
            "favorite_car_model": favorite_model["car_model__name"] if favorite_model else None,
        }


class SupplierStatsService:
    @staticmethod
    def get_supplier_stats(supplier_id):
        """Calculates all key statistics for a single Supplier."""

        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return None

        sales_data = Transaction.objects.filter(
            sender_content_type=SUPPLIER_CT, sender_object_id=supplier_id, transaction_type="PURCHASE"
        ).aggregate(
            total_sales=Coalesce(Sum("count"), 0, output_field=DecimalField()),
            total_revenue=Coalesce(Sum("amount"), 0, output_field=DecimalField()),
            partner_dealerships=Count("recipient_object_id", distinct=True),
        )

        active_promotions = supplier.actions.filter(is_active=True).count()

        offers_qs = supplier.car_offers.filter(is_active=True).aggregate(
            total_stock=Coalesce(Sum("stock_count"), 0, output_field=DecimalField()), active_offers_count=Count("id")
        )

        return {
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "total_sales": sales_data["total_sales"],
            "total_revenue": sales_data["total_revenue"],
            "active_offers": offers_qs["active_offers_count"],
            "total_stock": offers_qs["total_stock"],
            "partner_dealerships": sales_data["partner_dealerships"],
            "active_promotions": active_promotions,
        }


class GlobalStatsService:
    @staticmethod
    def get_global_stats():
        """Calculates global system statistics."""

        total_dealerships = Dealership.objects.count()
        total_suppliers = Supplier.objects.count()
        total_customers = CustomerProfile.objects.count()

        transactions_data = Transaction.objects.aggregate(
            total_transactions=Count("id"),
            total_transaction_volume=Coalesce(Sum("amount"), 0, output_field=DecimalField()),
            total_cars_sold=Coalesce(Sum("count", filter=Q(transaction_type="SALE")), 0, output_field=DecimalField()),
        )

        active_offers = Offer.objects.filter(status="PENDING").count()

        popularity = (
            Transaction.objects.values("car_model__name", "car_model__manufacturer")
            .annotate(total_count=Sum("count", filter=Q(transaction_type="SALE"), output_field=DecimalField()))
            .order_by("-total_count")
            .first()
        )

        return {
            "total_dealerships": total_dealerships,
            "total_suppliers": total_suppliers,
            "total_customers": total_customers,
            "total_transactions": transactions_data["total_transactions"],
            "total_transaction_volume": transactions_data["total_transaction_volume"],
            "total_cars_sold": transactions_data["total_cars_sold"],
            "active_offers": active_offers,
            "most_popular_car_model": popularity["car_model__name"] if popularity else None,
            "most_popular_manufacturer": popularity["car_model__manufacturer"] if popularity else None,
        }
