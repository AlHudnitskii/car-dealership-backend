from django.contrib.auth import get_user_model
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

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_customer=True,
            is_active=False,
        )
        CustomerProfile.objects.create(user=user)
        return user


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Customer Profile, including nested User details."""

    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ("id", "user", "user_details", "balance", "auto_generated_info", "created_at", "updated_at")
        read_only_fields = ("user", "balance", "auto_generated_info")
