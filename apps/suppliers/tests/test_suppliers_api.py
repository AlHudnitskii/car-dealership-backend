import pytest
from django.urls import reverse
from faker import Faker

from apps.suppliers.models import SupplierAction

pytestmark = pytest.mark.django_db
fake = Faker()


class TestSupplierViewSet:
    list_url = reverse("supplier-list")

    def test_list_suppliers_authenticated(self, api_client, regular_user, supplier_instance):
        """Authenticated users can view supplier list (read-only)."""

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == supplier_instance.name

    def test_create_supplier_superuser(self, superuser_client):
        """Only Superuser/Staff can create a Supplier."""
        new_data = {"name": "New Global Supplier", "year_founded": 2020, "info": "Test info"}
        response = superuser_client.post(self.list_url, new_data)
        assert response.status_code == 201
        assert response.data["name"] == "New Global Supplier"

    def test_create_supplier_supplier_admin_forbidden(self, supplier_auth_client):
        """Supplier admin cannot create new Supplier object (requires IsAdminUser)."""

        new_data = {"name": "Unauthorized Supplier", "year_founded": 2020}
        response = supplier_auth_client.post(self.list_url, new_data)
        assert response.status_code == 403


class TestSupplierCarOfferViewSet:
    list_url = reverse("supplieroffer-list")

    def test_list_offers_authenticated(self, api_client, regular_user, supplier_car_offer):
        """Authenticated users can view offers (ListSerializer)."""

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert "car_model_full_name" in response.data["results"][0]

    def test_create_offer_supplier_admin(self, supplier_auth_client, supplier_instance, car_model):
        """Supplier admin can create offers (ManageSerializer)."""

        new_data = {"supplier": supplier_instance.pk, "car_model": car_model.pk, "price": 18000.00, "stock_count": 5}
        response = supplier_auth_client.post(self.list_url, new_data)
        assert response.status_code == 201
        assert response.data["price"] == "18000.00"

    def test_update_offer_regular_user_forbidden(self, api_client, regular_user, supplier_car_offer):
        """Regular user cannot update offers."""

        api_client.force_authenticate(user=regular_user)
        detail_url = reverse("supplieroffer-detail", kwargs={"pk": supplier_car_offer.pk})
        response = api_client.patch(detail_url, {"price": 100.00})
        assert response.status_code == 403


class TestSupplierActionViewSet:
    list_url = reverse("supplieraction-list")

    def test_create_action_supplier_admin(self, supplier_auth_client, supplier_instance):
        """Supplier admin can create actions/promotions."""

        new_data = {
            "supplier": supplier_instance.pk,
            "name": "Test Action",
            "description": "Description",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2025-12-31T23:59:59Z",
            "discount_percentage": 15.00,
        }
        response = supplier_auth_client.post(self.list_url, new_data, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "Test Action"

    def test_list_actions_only_active_for_regular_user(self, api_client, regular_user, supplier_action):
        """Regular user only sees active actions."""

        supplier_action.is_active = False
        supplier_action.save()

        SupplierAction.objects.create(
            supplier=supplier_action.supplier,
            name="Active Action",
            description="Active",
            start_date=fake.past_datetime(),
            end_date=fake.future_datetime(),
            discount_percentage=10.00,
            is_active=True,
        )

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Active Action"
