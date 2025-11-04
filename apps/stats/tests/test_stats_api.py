from decimal import Decimal

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestStatsAPI:

    def test_global_stats_superuser_success(self, superuser_client, setup_dealership_transactions):
        """Superuser can access global statistics."""

        url = reverse("stats-global-stats")
        response = superuser_client.get(url)
        assert response.status_code == 200
        assert response.data["total_cars_sold"] == 1
        assert Decimal(response.data["total_transaction_volume"]) == Decimal("40000.00")

    def test_dealership_stats_admin_access(
        self, api_client, superuser, dealership_instance, setup_dealership_transactions
    ):
        """Dealership admin (superuser in this case) can access their stats."""

        dealership_instance.admin = superuser
        dealership_instance.save()

        api_client.force_authenticate(user=super)
        url = reverse("stats-dealership-stats", kwargs={"dealership_pk": dealership_instance.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["total_cars_sold"] == 1
        assert Decimal(response.data["net_profit"]) == Decimal("10000.00")
        assert response.data["unique_customers"] == 1

    def test_customer_stats_owner_access(
        self, api_client, regular_user, test_customer_profile, setup_dealership_transactions
    ):
        """Customer can access their own statistics."""

        api_client.force_authenticate(user=regular_user)
        url = reverse("stats-my-stats")
        response = api_client.get(url)

        assert response.status_code == 200
        assert Decimal(response.data["total_spent"]) == Decimal("25000.00")
        assert response.data["pending_offers"] == 1
        assert response.data["rejected_offers"] == 1
        assert response.data["customer_email"] == regular_user.email

    def test_supplier_stats_superuser_access(self, superuser_client, test_supplier, setup_dealership_transactions):
        """Superuser can access supplier statistics."""

        url = reverse("stats-supplier-stats", kwargs={"supplier_pk": test_supplier.pk})
        response = superuser_client.get(url)

        assert response.status_code == 200
        assert response.data["total_sales"] == 1
        assert Decimal(response.data["total_revenue"]) == Decimal("15000.00")
        assert response.data["partner_dealerships"] == 1
