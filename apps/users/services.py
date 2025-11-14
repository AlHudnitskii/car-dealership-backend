from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_change_token, email_confirmation_token, password_reset_token


class EmailService:
    """Service for sending authentication emails."""

    @staticmethod
    def send_email_confirmation(user, request=None):
        token = email_confirmation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if request:
            base_url = request.build_absolute_uri("/")[:-1]
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:8000")

        confirmation_url = f"{base_url}/api/auth/confirm-email/{uid}/{token}/"

        context = {
            "user": user,
            "confirmation_url": confirmation_url,
        }

        subject = "Confirm Your Email - Car Dealership"
        message = render_to_string("users/email_confirmation.txt", context)
        html_message = render_to_string("users/email_confirmation.html", context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def send_password_reset_email(user, request=None):
        token = password_reset_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if request:
            base_url = request.build_absolute_uri("/")[:-1]
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:8000")

        reset_url = f"{base_url}/api/auth/password-reset-confirm/{uid}/{token}/"

        context = {
            "user": user,
            "reset_url": reset_url,
        }

        subject = "Password Reset - Car Dealership"
        message = render_to_string("users/password_reset.txt", context)
        html_message = render_to_string("users/password_reset.html", context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def send_email_change_confirmation(user, new_email, request=None):
        token = email_change_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if request:
            base_url = request.build_absolute_uri("/")[:-1]
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:8000")

        from django.core.cache import cache

        cache_key = f"email_change_{user.pk}_{token}"
        cache.set(cache_key, new_email, timeout=3600)

        confirmation_url = f"{base_url}/api/auth/confirm-email-change/{uid}/{token}/"

        context = {
            "user": user,
            "new_email": new_email,
            "confirmation_url": confirmation_url,
        }

        subject = "Confirm Email Change - Car Dealership"
        message = render_to_string("users/email_change_confirmation.txt", context)
        html_message = render_to_string("users/email_change_confirmation.html", context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def send_password_changed_notification(user):
        context = {"user": user}

        subject = "Password Changed - Car Dealership"
        message = render_to_string("users/password_changed.txt", context)
        html_message = render_to_string("users/password_changed.html", context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
