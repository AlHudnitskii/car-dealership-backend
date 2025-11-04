from rest_framework import serializers

from .models import Supplier, SupplierAction, SupplierCarOffer


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model (List and Detail)."""

    active_offers_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = ("id", "name", "year_founded", "info", "is_active", "created_at", "active_offers_count")
        read_only_fields = ("active_offers_count",)

    def get_active_offers_count(self, obj):
        """Returns the count of active car offers from this supplier."""
        return obj.car_offers.filter(is_active=True).count()


class SupplierCarOfferListSerializer(serializers.ModelSerializer):
    """Serializer for listing SupplierCarOffer (read-only for customers/dealerships)."""

    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    car_model_full_name = serializers.ReadOnlyField(source="car_model.__str__")

    class Meta:
        model = SupplierCarOffer
        fields = (
            "id",
            "supplier",
            "supplier_name",
            "car_model",
            "car_model_full_name",
            "price",
            "stock_count",
            "is_active",
        )


class SupplierCarOfferManageSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating SupplierCarOffer (for supplier admins)."""

    class Meta:
        model = SupplierCarOffer
        fields = (
            "id",
            "supplier",
            "car_model",
            "price",
            "stock_count",
            "is_active",
        )


class SupplierActionSerializer(serializers.ModelSerializer):
    """Serializer for SupplierAction (promotions)."""

    supplier_name = serializers.ReadOnlyField(source="supplier.name")

    class Meta:
        model = SupplierAction
        fields = (
            "id",
            "supplier",
            "supplier_name",
            "name",
            "description",
            "start_date",
            "end_date",
            "discount_percentage",
            "is_active",
        )
