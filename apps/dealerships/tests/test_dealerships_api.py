import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestDealershipViewSet:
    list_url = reverse("dealership-list")

    def test_list_dealerships_unauthenticated(self, api_client, dealership_instance):
        """Unauthenticated users should get 401."""

        response = api_client.get(self.list_url)
        assert response.status_code == 401

    def test_list_dealerships_regular_user(self, auth_client, dealership_instance):
        """Regular users (or admin user when listing all) should see active dealerships."""

        response = auth_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert "admin_email" in response.data["results"][0]

    def test_retrieve_dealership_admin_owner(self, auth_client, dealership_instance):
        """Dealership admin should retrieve his dealership details (DetailSerializer)."""

        detail_url = reverse("dealership-detail", kwargs={"pk": dealership_instance.pk})
        response = auth_client.get(detail_url)
        assert response.status_code == 200
        assert "admin_info" in response.data
        assert response.data["name"] == dealership_instance.name

    def test_create_dealership_superuser(self, superuser_client, create_user):
        """Superuser should be able to create a new dealership."""

        new_admin = create_user(is_dealership_admin=True, email="new@admin.com")
        new_data = {
            "name": "New Super Deal",
            "country": "CA",
            "city": "Toronto",
            "address": "123 Test St",
            "admin": new_admin.pk,
        }
        response = superuser_client.post(self.list_url, new_data)
        assert response.status_code == 201
        assert response.data["name"] == "New Super Deal"

    def test_update_dealership_owner(self, auth_client, dealership_instance):
        """Dealership admin should be able to update his own dealership (permission IsDealershipOwner)."""
        detail_url = reverse("dealership-detail", kwargs={"pk": dealership_instance.pk})
        updated_data = {"name": "Updated Name", "city": "New City"}
        response = auth_client.patch(detail_url, updated_data, format="json")
        assert response.status_code == 200
        dealership_instance.refresh_from_db()
        assert dealership_instance.name == "Updated Name"

    def test_update_dealership_not_owner(self, api_client, dealership_instance, regular_user):
        """Regular user/non-admin should not be able to update."""
        api_client.force_authenticate(user=regular_user)
        detail_url = reverse("dealership-detail", kwargs={"pk": dealership_instance.pk})
        updated_data = {"name": "Tried to Update"}
        response = api_client.patch(detail_url, updated_data)
        assert response.status_code == 403


class TestDealershipActionViewSet:
    list_url = reverse("dealershipaction-list")

    def test_list_actions_unauthenticated(self, api_client, dealership_action):
        """Unauthenticated users should get 401."""

        response = api_client.get(self.list_url)
        assert response.status_code == 401

    def test_list_actions_authenticated(self, auth_client, dealership_action):
        """Authenticated users should see actions."""

        response = auth_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_create_action_admin(self, auth_client, dealership_instance, car_model):
        """Dealership admin should be able to create an action (IsDealershipStaff)."""

        new_data = {
            "dealership": dealership_instance.pk,
            "name": "New Promo",
            "description": "Test",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2025-12-31T23:59:59Z",
            "discount_percentage": 5.00,
            "car_models": [car_model.pk],
        }
        response = auth_client.post(self.list_url, new_data, format="json")
        assert response.status_code == 201
        assert response.data["name"] == "New Promo"

    def test_create_action_regular_user(self, api_client, dealership_instance, car_model, regular_user):
        """Regular user should not be able to create an action."""

        api_client.force_authenticate(user=regular_user)
        new_data = {
            "dealership": dealership_instance.pk,
            "name": "Fraud Promo",
            "description": "Test1",
            "start_date": "2025-02-01T00:00:00Z",
            "end_date": "2025-12-30T23:59:59Z",
            "discount_percentage": 5.00,
            "car_models": [car_model.pk],
        }
        response = api_client.post(self.list_url, new_data)
        assert response.status_code == 403
