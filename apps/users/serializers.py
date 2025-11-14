from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomerProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for general User details (for Staff/Admins)."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "is_superuser",
            "is_staff",
            "is_customer",
            "is_dealership_admin",
            "is_supplier_admin",
            "email_confirmed",
            "date_joined",
        )
        read_only_fields = ("email_confirmed", "date_joined")


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Customer Registration."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"}, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "first_name", "last_name")

    def validate(self, data):
        """Validate passwords match."""
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_customer=True,
            is_active=True,
            email_confirmed=False,
        )
        CustomerProfile.objects.create(user=user)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password for authenticated users."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        """Validate passwords match."""
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data

    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset."""

    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        """Validate passwords match."""
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data


class EmailChangeSerializer(serializers.Serializer):
    """Serializer for requesting email change."""

    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        """Validate new email is not already in use."""
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email address is already in use.")
        if value == user.email:
            raise serializers.ValidationError("New email must be different from current email.")
        return value


class UsernameChangeSerializer(serializers.Serializer):
    """Serializer for changing username."""

    new_username = serializers.CharField(max_length=150)

    def validate_new_username(self, value):
        """Validate new username is not already in use."""
        user = self.context["request"].user
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This username is already in use.")
        if value == user.username:
            raise serializers.ValidationError("New username must be different from current username.")
        return value


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Customer Profile, including nested User details."""

    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ("id", "user", "user_details", "balance", "auto_generated_info", "created_at", "updated_at")
        read_only_fields = ("user", "balance", "auto_generated_info")
