import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestCarSpecificationViewSet:
    list_url = reverse("carspecification-list")

    def test_list_specs_authenticated(self, api_client, regular_user, car_specification):
        """Authenticated users can view specs (read-only)."""

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["engine_type"] == "Petrol"

    def test_create_spec_superuser(self, superuser_client, spec_data):
        """Superuser/Staff can create specs."""

        response = superuser_client.post(self.list_url, spec_data)
        assert response.status_code == 201
        assert response.data["engine_type"] == "Electric"

    def test_create_spec_regular_user_forbidden(self, regular_client, spec_data):
        """Regular user cannot create specs."""

        response = regular_client.post(self.list_url, spec_data)
        assert response.status_code == 403


class TestCarModelViewSet:
    list_url = reverse("carmodel-list")

    def test_list_models_authenticated(self, api_client, regular_user, car_model):
        """Authenticated users can view models (List/Create Serializer)."""

        api_client.force_authenticate(user=regular_user)
        response = api_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["manufacturer"] == "Audi"
        assert "full_name" in response.data["results"][0]

    def test_retrieve_model_authenticated(self, regular_client, car_model):
        """Authenticated users can retrieve model detail (Detail Serializer)."""

        detail_url = reverse("carmodel-detail", kwargs={"pk": car_model.pk})
        response = regular_client.get(detail_url)
        assert response.status_code == 200
        assert "base_specs" in response.data
        assert response.data["base_specs"]["power_hp"] == 200

    def test_create_model_superuser(self, superuser_client, car_specification):
        """Superuser/Staff can create models."""

        new_data = {"name": "Model X", "manufacturer": "Tesla", "base_specs": car_specification.pk}
        response = superuser_client.post(self.list_url, new_data)
        assert response.status_code == 201
        assert response.data["manufacturer"] == "Tesla"

    def test_update_model_regular_user_forbidden(self, regular_client, car_model):
        """Regular user cannot update models."""

        detail_url = reverse("carmodel-detail", kwargs={"pk": car_model.pk})
        response = regular_client.patch(detail_url, {"manufacturer": "Fake"})
        assert response.status_code == 403
