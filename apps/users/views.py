from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import CustomerProfile
from .permissions import IsCustomerOwner
from .serializers import (
    CustomerProfileSerializer,
    EmailChangeSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UsernameChangeSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from .services import EmailService
from .tokens import email_change_token, email_confirmation_token, password_reset_token

User = get_user_model()


class UserViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API for viewing User list and details.
    Access: Staff/Superuser for list/retrieve, or retrieve own profile.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list"]:
            permission_classes = [IsAdminUser]
        elif self.action in ["retrieve", "me"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all()
        if self.action == "retrieve":
            return User.objects.filter(pk=user.pk)
        return User.objects.none()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """View the authenticated user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication-related actions:
    - Password change
    - Password reset request/confirm
    - Email confirmation
    - Email change
    - Username change
    """

    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"], url_path="password-change", permission_classes=[IsAuthenticated])
    def password_change(self, request):
        """
        Change password for authenticated user.
        Requires old password verification.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        try:
            EmailService.send_password_changed_notification(user)
        except Exception as e:
            print(f"Failed to send password change notification: {e}")

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="password-reset-request")
    def password_reset_request(self, request):
        """
        Request password reset email.
        Always returns success to prevent email enumeration.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)
            EmailService.send_password_reset_email(user, request)
        except User.DoesNotExist:
            pass
        return Response(
            {"detail": "If an account exists with this email, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path=r"password-reset-confirm/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)")
    def password_reset_confirm(self, request, uidb64=None, token=None):
        """
        Confirm password reset with token from email.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not password_reset_token.check_token(user, token):
            return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        try:
            EmailService.send_password_changed_notification(user)
        except Exception as e:
            print(f"Failed to send notification: {e}")

        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path=r"confirm-email/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)")
    def confirm_email(self, request, uidb64=None, token=None):
        """
        Confirm user's email address using token from registration email.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid confirmation link."}, status=status.HTTP_400_BAD_REQUEST)

        if user.email_confirmed:
            return Response({"detail": "Email already confirmed."}, status=status.HTTP_200_OK)

        if not email_confirmation_token.check_token(user, token):
            return Response({"detail": "Invalid or expired confirmation link."}, status=status.HTTP_400_BAD_REQUEST)

        user.email_confirmed = True
        user.save()

        return Response({"detail": "Email confirmed successfully. You can now log in."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="resend-confirmation", permission_classes=[IsAuthenticated])
    def resend_confirmation(self, request):
        """
        Resend email confirmation link.
        """
        user = request.user

        if user.email_confirmed:
            return Response({"detail": "Email is already confirmed."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            EmailService.send_email_confirmation(user, request)
        except Exception as e:
            return Response(
                {"detail": f"Failed to send confirmation email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"detail": "Confirmation email has been resent."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="email-change-request", permission_classes=[IsAuthenticated])
    def email_change_request(self, request):
        """
        Request email change. Sends confirmation link to NEW email.
        """
        serializer = EmailChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data["new_email"]

        try:
            EmailService.send_email_change_confirmation(request.user, new_email, request)
        except Exception as e:
            return Response(
                {"detail": f"Failed to send confirmation email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"detail": f"Confirmation link has been sent to {new_email}."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path=r"confirm-email-change/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)")
    def confirm_email_change(self, request, uidb64=None, token=None):
        """
        Confirm email change using token from confirmation email.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid confirmation link."}, status=status.HTTP_400_BAD_REQUEST)

        if not email_change_token.check_token(user, token):
            return Response({"detail": "Invalid or expired confirmation link."}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"email_change_{user.pk}_{token}"
        new_email = cache.get(cache_key)

        if not new_email:
            return Response({"detail": "Confirmation link has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            cache.delete(cache_key)
            return Response(
                {"detail": "This email address is no longer available."}, status=status.HTTP_400_BAD_REQUEST
            )

        user.email = new_email
        user.email_confirmed = True
        user.save()

        cache.delete(cache_key)

        return Response({"detail": "Email changed successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="username-change", permission_classes=[IsAuthenticated])
    def username_change(self, request):
        """
        Change username (no confirmation needed).
        """
        serializer = UsernameChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.username = serializer.validated_data["new_username"]
        user.save()

        return Response({"detail": "Username changed successfully."}, status=status.HTTP_200_OK)


class CustomerProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    API for managing Customer Profiles.
    Access: Staff/Superuser for list/full CRUD. Retrieve own profile for Customer.
    """

    queryset = CustomerProfile.objects.all().select_related("user")
    serializer_class = CustomerProfileSerializer

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        elif self.action == "retrieve":
            permission_classes = [IsAuthenticated, IsCustomerOwner]
        else:
            permission_classes = [IsAdminUser]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions

    @action(detail=False, methods=["post"], url_path="register", permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Public endpoint for customer registration."""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            EmailService.send_email_confirmation(user, request)
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")

        return Response(
            {"detail": "Registration successful. Please check your email to confirm your account."},
            status=status.HTTP_201_CREATED,
        )
