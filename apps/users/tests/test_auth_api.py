import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.users.tokens import email_confirmation_token, password_reset_token

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestAuthRegistration:
    """Tests for user registration."""

    register_url = reverse("customer-register")

    def test_registration_success(self, api_client):
        """Test successful user registration."""
        data = {
            "email": "newuser@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = api_client.post(self.register_url, data)

        assert response.status_code == 201
        assert "check your email" in response.data["detail"].lower()

        user = User.objects.get(email="newuser@test.com")
        assert user.is_customer
        assert user.is_active
        assert not user.email_confirmed
        assert user.check_password("StrongPass123!")

        assert len(mail.outbox) == 1
        assert "Confirm Your Email" in mail.outbox[0].subject

    def test_registration_password_mismatch(self, api_client):
        """Test registration fails with password mismatch."""
        data = {
            "email": "test@test.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
            "first_name": "John",
        }
        response = api_client.post(self.register_url, data)

        assert response.status_code == 400
        assert "do not match" in str(response.data).lower()

    def test_registration_duplicate_email(self, api_client, regular_user):
        """Test registration fails with duplicate email."""
        data = {
            "email": regular_user.email,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = api_client.post(self.register_url, data)

        assert response.status_code == 400


class TestEmailConfirmation:
    """Tests for email confirmation."""

    def test_confirm_email_success(self, api_client, regular_user):
        """Test successful email confirmation."""
        regular_user.email_confirmed = False
        regular_user.save()

        token = email_confirmation_token.make_token(regular_user)
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))

        url = reverse("auth-confirm-email", kwargs={"uidb64": uid, "token": token})
        response = api_client.get(url)

        assert response.status_code == 200
        assert "confirmed successfully" in response.data["detail"].lower()

        regular_user.refresh_from_db()
        assert regular_user.email_confirmed

    def test_confirm_email_invalid_token(self, api_client, regular_user):
        """Test email confirmation fails with invalid token."""
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))
        url = reverse("auth-confirm-email", kwargs={"uidb64": uid, "token": "invalid-token"})

        response = api_client.get(url)
        assert response.status_code == 400

    def test_resend_confirmation(self, regular_client, regular_user):
        """Test resending confirmation email."""
        regular_user.email_confirmed = False
        regular_user.save()

        url = reverse("auth-resend-confirmation")
        response = regular_client.post(url)

        assert response.status_code == 200
        assert len(mail.outbox) == 1

    def test_resend_confirmation_already_confirmed(self, regular_client, regular_user):
        """Test resending confirmation when already confirmed."""
        regular_user.email_confirmed = True
        regular_user.save()

        url = reverse("auth-resend-confirmation")
        response = regular_client.post(url)

        assert response.status_code == 400


class TestPasswordChange:
    """Tests for password change."""

    password_change_url = reverse("auth-password-change")

    def test_password_change_success(self, regular_client, regular_user):
        """Test successful password change."""
        data = {
            "old_password": "testpass123",
            "new_password": "NewStrongPass123!",
            "new_password_confirm": "NewStrongPass123!",
        }
        response = regular_client.post(self.password_change_url, data)

        assert response.status_code == 200
        assert "changed successfully" in response.data["detail"].lower()

        regular_user.refresh_from_db()
        assert regular_user.check_password("NewStrongPass123!")

        assert len(mail.outbox) == 1
        assert "Password Changed" in mail.outbox[0].subject

    def test_password_change_wrong_old_password(self, regular_client):
        """Test password change fails with wrong old password."""
        data = {
            "old_password": "wrongpassword",
            "new_password": "NewStrongPass123!",
            "new_password_confirm": "NewStrongPass123!",
        }
        response = regular_client.post(self.password_change_url, data)

        assert response.status_code == 400
        assert "incorrect" in str(response.data).lower()

    def test_password_change_mismatch(self, regular_client):
        """Test password change fails with password mismatch."""
        data = {
            "old_password": "testpass123",
            "new_password": "NewPass123!",
            "new_password_confirm": "DifferentPass123!",
        }
        response = regular_client.post(self.password_change_url, data)

        assert response.status_code == 400


class TestPasswordReset:
    """Tests for password reset flow."""

    reset_request_url = reverse("auth-password-reset-request")

    def test_password_reset_request(self, api_client, regular_user):
        """Test password reset request."""
        data = {"email": regular_user.email}
        response = api_client.post(self.reset_request_url, data)

        assert response.status_code == 200
        assert len(mail.outbox) == 1
        assert "Password Reset" in mail.outbox[0].subject

    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test password reset request with non-existent email."""
        data = {"email": "nonexistent@test.com"}
        response = api_client.post(self.reset_request_url, data)

        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_password_reset_confirm_success(self, api_client, regular_user):
        """Test successful password reset confirmation."""
        token = password_reset_token.make_token(regular_user)
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))

        url = reverse("auth-password-reset-confirm", kwargs={"uidb64": uid, "token": token})
        data = {
            "new_password": "NewResetPass123!",
            "new_password_confirm": "NewResetPass123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == 200

        regular_user.refresh_from_db()
        assert regular_user.check_password("NewResetPass123!")

    def test_password_reset_confirm_invalid_token(self, api_client, regular_user):
        """Test password reset fails with invalid token."""
        uid = urlsafe_base64_encode(force_bytes(regular_user.pk))
        url = reverse("auth-password-reset-confirm", kwargs={"uidb64": uid, "token": "invalid-token"})

        data = {
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == 400


class TestEmailChange:
    """Tests for email change."""

    email_change_request_url = reverse("auth-email-change-request")

    def test_email_change_request(self, regular_client, regular_user):
        """Test email change request."""
        data = {"new_email": "newemail@test.com"}
        response = regular_client.post(self.email_change_request_url, data)

        assert response.status_code == 200
        assert "sent to newemail@test.com" in response.data["detail"]
        assert len(mail.outbox) == 1

    def test_email_change_duplicate(self, regular_client, other_user):
        """Test email change fails with duplicate email."""
        data = {"new_email": other_user.email}
        response = regular_client.post(self.email_change_request_url, data)

        assert response.status_code == 400
        assert "already in use" in str(response.data).lower()

    def test_email_change_same_email(self, regular_client, regular_user):
        """Test email change fails when new email is same as current."""
        data = {"new_email": regular_user.email}
        response = regular_client.post(self.email_change_request_url, data)

        assert response.status_code == 400


class TestUsernameChange:
    """Tests for username change."""

    username_change_url = reverse("auth-username-change")

    def test_username_change_success(self, regular_client, regular_user):
        """Test successful username change."""
        data = {"new_username": "newusername"}
        response = regular_client.post(self.username_change_url, data)

        assert response.status_code == 200

        regular_user.refresh_from_db()
        assert regular_user.username == "newusername"

    def test_username_change_duplicate(self, regular_client, other_user):
        """Test username change fails with duplicate username."""
        data = {"new_username": other_user.username}
        response = regular_client.post(self.username_change_url, data)

        assert response.status_code == 400


class TestOfferCreationRestriction:
    """Tests for offer creation restriction based on email confirmation."""

    def test_create_offer_without_confirmed_email(self, regular_client, customer_profile, car_model):
        """Test that offer creation fails without confirmed email."""
        customer_profile.user.email_confirmed = False
        customer_profile.user.save()
        customer_profile.balance = 50000.00
        customer_profile.save()

        url = reverse("offer-list")
        data = {"car_model": car_model.pk, "max_price": 25000.00}
        response = regular_client.post(url, data)

        assert response.status_code == 403

    def test_create_offer_with_confirmed_email(self, regular_client, customer_profile, car_model):
        """Test that offer creation succeeds with confirmed email."""
        customer_profile.user.email_confirmed = True
        customer_profile.user.save()
        customer_profile.balance = 50000.00
        customer_profile.save()

        url = reverse("offer-list")
        data = {"car_model": car_model.pk, "max_price": 25000.00}
        response = regular_client.post(url, data)

        assert response.status_code == 201
