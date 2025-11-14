from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email confirmation.
    Inherits from Django's PasswordResetTokenGenerator to leverage its secure token generation.
    """

    def _make_hash_value(self, user, timestamp):
        email_confirmed = "" if user.email_confirmed else "not_confirmed"
        return f"{user.pk}{timestamp}{user.is_active}{email_confirmed}"


class PasswordResetTokenGeneratorWithExpiry(PasswordResetTokenGenerator):
    """
    Token generator for password reset with enhanced security.
    Inherits from Django's PasswordResetTokenGenerator to leverage its secure token generation.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{timestamp}{user.last_login or ''}"


class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email change confirmation.
    Inherits from Django's PasswordResetTokenGenerator to leverage its secure token generation.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.email}{timestamp}"


email_confirmation_token = EmailConfirmationTokenGenerator()
password_reset_token = PasswordResetTokenGeneratorWithExpiry()
email_change_token = EmailChangeTokenGenerator()
