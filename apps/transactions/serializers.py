from rest_framework import serializers

from .models import Offer


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new Offer."""

    class Meta:
        model = Offer
        fields = ("id", "car_model", "max_price")
        read_only_fields = ("status", "dealership_match")

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_customer:
            raise serializers.ValidationError("Only customers can create Offers.")

        customer_profile = user.customer_profile

        if customer_profile.balance < data["max_price"]:
            raise serializers.ValidationError("Insufficient balance for this offer.")

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        customer_profile = user.customer_profile
        return Offer.objects.create(customer=customer_profile, **validated_data)


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for viewing Offer."""

    customer_email = serializers.ReadOnlyField(source="customer.user.email")

    class Meta:
        model = Offer
        fields = ("id", "car_model", "max_price", "status", "dealership_match", "customer_email", "created_at")
