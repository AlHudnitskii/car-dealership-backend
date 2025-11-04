import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.users.models import CustomerProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserViewSet:
    list_url = reverse("user-list")

    def test_retrieve_me(self, regular_client, regular_user_confirmed):
        """Authenticated user can view their own profile via /me."""

        response = regular_client.get(reverse("user-me"))
        assert response.status_code == 200
        assert response.data["email"] == regular_user_confirmed.email

    def test_list_users_regular_user_forbidden(self, regular_client):
        """Regular user cannot list all users."""

        response = regular_client.get(self.list_url)
        assert response.status_code == 403

    def test_list_users_superuser(self, superuser_client, regular_user_confirmed, other_user):
        """Superuser can list all users."""

        response = superuser_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) >= 3

    def test_retrieve_user_superuser_can_see_all(self, superuser_client, other_user):
        """Superuser can retrieve any user profile."""

        detail_url = reverse("user-detail", kwargs={"pk": other_user.pk})
        response = superuser_client.get(detail_url)
        assert response.status_code == 200
        assert response.data["email"] == other_user.email


class TestCustomerProfileViewSet:
    register_url = reverse("customer-register")
    list_url = reverse("customer-list")

    def test_register_new_customer(self, api_client):
        """Anyone can hit the register endpoint."""

        data = {
            "email": "new_customer@example.com",
            "password": "strongpassword123",
            "first_name": "New",
        }
        response = api_client.post(self.register_url, data)

        assert response.status_code == 201
        assert "Registration successful" in response.data["results"]["detail"]

        new_user = User.objects.get(email="new_customer@example.com")
        assert new_user.is_customer is True
        assert new_user.is_active is False
        assert CustomerProfile.objects.filter(user=new_user).exists()

    def test_retrieve_own_profile(self, regular_client, customer_profile_instance):
        """Customer can retrieve their own profile."""

        detail_url = reverse("customer-detail", kwargs={"pk": customer_profile_instance.pk})
        response = regular_client.get(detail_url)
        assert response.status_code == 200
        assert response.data["user_details"]["email"] == customer_profile_instance.user.email

    def test_retrieve_other_profile_forbidden(self, regular_client, other_user):
        """Customer cannot retrieve another customer's profile."""

        other_profile = CustomerProfile.objects.get_or_create(user=other_user)[0]
        detail_url = reverse("customer-detail", kwargs={"pk": other_profile.pk})

        response = regular_client.get(detail_url)
        assert response.status_code == 403
