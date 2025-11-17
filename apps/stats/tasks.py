import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

from apps.dealerships.models import Dealership
from apps.suppliers.models import Supplier
from apps.transactions.models import Transaction
from apps.users.models import CustomerProfile

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_daily_reports(self):
    """
    Generate daily reports and save them to the cache.
    Called every day at 11:50 PM.
    """
    logger.info("Starting daily reports generation")

    today = timezone.now().date()
    start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_of_day = timezone.now()

    reports = {
        "date": str(today),
        "dealerships": generate_dealerships_report(start_of_day, end_of_day),
        "suppliers": generate_suppliers_report(start_of_day, end_of_day),
        "customers": generate_customers_report(start_of_day, end_of_day),
        "transactions": generate_transactions_report(start_of_day, end_of_day),
    }

    cache.set(f"daily_report_{today}", reports, timeout=604800)

    logger.info(f"Daily report generated for {today}")

    return reports


def generate_dealerships_report(start_time, end_time):
    """Daily car dealership report."""
    dealership_ct = ContentType.objects.get_for_model(Dealership)

    sales = Transaction.objects.filter(
        sender_content_type=dealership_ct, transaction_type="SALE", created_at__range=(start_time, end_time)
    ).aggregate(total_sales=Count("id"), total_revenue=Sum("amount"), total_cars_sold=Sum("count"))

    purchases = Transaction.objects.filter(
        recipient_content_type=dealership_ct, transaction_type="PURCHASE", created_at__range=(start_time, end_time)
    ).aggregate(total_purchases=Count("id"), total_expenses=Sum("amount"), total_cars_bought=Sum("count"))

    return {
        "sales": sales,
        "purchases": purchases,
        "active_dealerships": Dealership.objects.filter(is_active=True).count(),
    }


def generate_suppliers_report(start_time, end_time):
    """Daily car supplier report."""
    supplier_ct = ContentType.objects.get_for_model(Supplier)

    sales = Transaction.objects.filter(
        sender_content_type=supplier_ct, transaction_type="PURCHASE", created_at__range=(start_time, end_time)
    ).aggregate(total_sales=Count("id"), total_revenue=Sum("amount"), total_cars_sold=Sum("count"))

    return {"sales": sales, "active_suppliers": Supplier.objects.filter(is_active=True).count()}


def generate_customers_report(start_time, end_time):
    """Daily customer report."""
    customer_ct = ContentType.objects.get_for_model(CustomerProfile)

    purchases = Transaction.objects.filter(
        recipient_content_type=customer_ct, transaction_type="SALE", created_at__range=(start_time, end_time)
    ).aggregate(
        total_purchases=Count("id"),
        total_spent=Sum("amount"),
        total_cars_bought=Sum("count"),
        unique_customers=Count("recipient_object_id", distinct=True),
    )

    return {"purchases": purchases, "active_customers": CustomerProfile.objects.filter(is_active=True).count()}


def generate_transactions_report(start_time, end_time):
    """Daily transaction report."""
    total_transactions = Transaction.objects.filter(created_at__range=(start_time, end_time)).aggregate(
        count=Count("id"), volume=Sum("amount")
    )

    return total_transactions


@shared_task(bind=True)
def cache_popular_stats(self):
    """
    Caching frequently requested statistics.
    This is performed periodically to speed up API responses.
    """
    logger.info("Caching popular statistics")

    from .services import GlobalStatsService

    global_stats = GlobalStatsService.get_global_stats()
    cache.set("global_stats", global_stats, timeout=3600)

    dealership_ct = ContentType.objects.get_for_model(Dealership)

    top_dealerships = (
        Transaction.objects.filter(
            sender_content_type=dealership_ct,
            transaction_type="SALE",
            created_at__gte=timezone.now() - timedelta(days=30),
        )
        .values("sender_object_id")
        .annotate(total_sales=Sum("amount"), cars_sold=Sum("count"))
        .order_by("-total_sales")[:10]
    )

    cache.set("top_dealerships", list(top_dealerships), timeout=3600)

    logger.info("Statistics cached successfully")

    return {"cached": True}


@shared_task(bind=True)
def cleanup_old_reports(self):
    """
    Clear old reports from cache (older than 30 days).
    """
    logger.info("Cleaning up old reports")

    cleaned = 0
    thirty_days_ago = timezone.now().date() - timedelta(days=30)

    for i in range(60):
        date = thirty_days_ago - timedelta(days=i)
        key = f"daily_report_{date}"

        if cache.delete(key):
            cleaned += 1

    logger.info(f"Cleaned {cleaned} old reports")

    return {"cleaned": cleaned}
