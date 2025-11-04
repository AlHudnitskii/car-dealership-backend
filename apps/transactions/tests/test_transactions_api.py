import pytest
from django.urls import reverse

from apps.transactions.models import Offer

pytestmark = pytest.mark.django_db


class TestOfferViewSet:
    list_url = reverse("offer-list")

    def test_create_offer_success(self, regular_client, customer_profile, car_model):
        """Customer with enough balance and confirmed email can create an Offer."""

        customer_profile.user.email_confirmed = True
        customer_profile.user.save()
        customer_profile.balance = 30000.00
        customer_profile.save()

        new_offer_data = {"car_model": car_model.pk, "max_price": 25000.00}
        response = regular_client.post(self.list_url, new_offer_data, format="json")
        assert response.status_code == 201
        assert response.data["max_price"] == "25000.00"
        assert Offer.objects.count() == 1

    def test_create_offer_insufficient_balance(self, regular_client, customer_profile, car_model):
        """Should fail if customer balance is too low."""

        customer_profile.user.email_confirmed = True
        customer_profile.user.save()
        customer_profile.balance = 100.00
        customer_profile.save()

        new_offer_data = {"car_model": car_model.pk, "max_price": 25000.00}
        response = regular_client.post(self.list_url, new_offer_data, format="json")
        assert response.status_code == 400
        assert "Insufficient balance" in str(response.data)

    def test_list_offers_customer_only_own(self, regular_client, offer_instance, create_user, car_model):
        """Customer only sees their own offers."""

        other_user = create_user(email="other@test.com", is_customer=True)
        from apps.users.models import CustomerProfile

        other_customer = CustomerProfile.objects.create(user=other_user, balance=50000.00)
        Offer.objects.create(customer=other_customer, car_model=car_model, max_price=1000)

        response = regular_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == offer_instance.pk


class TestTransactionViewSet:
    list_url = reverse("transaction-list")

    def test_list_transactions_superuser(self, superuser_client, transaction_instance):
        """Superuser can see all transactions."""

        response = superuser_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert "sender_representation" in response.data[0]

    def test_list_transactions_owner_only_own(self, regular_client, transaction_instance, create_user):
        """Customer can only see transactions where they are sender or recipient."""

        response = regular_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data[0]["id"] == transaction_instance.pk

    def test_list_transactions_not_party_forbidden(self, regular_client, transaction_instance, create_user):
        """User who is not a party to the transaction should see nothing."""

        non_party_user = create_user(email="stranger@test.com")
        regular_client.force_authenticate(user=non_party_user)

        response = regular_client.get(self.list_url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 0

    def test_create_transaction_forbidden(self, superuser_client, car_model):
        """Creating transactions via API should be forbidden (ReadOnlyViewSet)."""

        response = superuser_client.post(self.list_url, {})
        assert response.status_code == 405
