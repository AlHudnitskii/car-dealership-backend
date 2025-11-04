from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stats"
    verbose_name = "Statistics"

    def ready(self):
        from django.contrib.contenttypes.models import ContentType

        from apps.dealerships.models import Dealership
        from apps.suppliers.models import Supplier
        from apps.users.models import CustomerProfile

        from . import services

        services.DEALERSHIP_CT = ContentType.objects.get_for_model(Dealership)
        services.CUSTOMER_CT = ContentType.objects.get_for_model(CustomerProfile)
        services.SUPPLIER_CT = ContentType.objects.get_for_model(Supplier)
