from rest_framework import serializers

from .models import CarModel, CarSpecification


class CarSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for CarSpecification model."""

    class Meta:
        model = CarSpecification
        fields = ("id", "engine_type", "power_hp", "color", "transmission", "body_type", "is_active")


class CarModelDetailSerializer(serializers.ModelSerializer):
    """Serializer for CarModel detail view, including nested specifications."""

    base_specs = CarSpecificationSerializer(read_only=True)

    class Meta:
        model = CarModel
        fields = ("id", "name", "manufacturer", "base_specs", "is_active", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class CarModelListCreateSerializer(serializers.ModelSerializer):
    """Serializer for CarModel list view and creation (uses only base_specs ID)."""

    full_name = serializers.ReadOnlyField(source="__str__")

    class Meta:
        model = CarModel
        fields = ("id", "name", "manufacturer", "base_specs", "is_active", "full_name")
