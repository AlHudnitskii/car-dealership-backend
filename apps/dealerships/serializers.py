from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from apps.vehicles.serializers import CarSpecificationSerializer

from .models import (
    Dealership,
    DealershipAction,
    DealershipCarInventory,
    DealershipPreferredSupplier,
)


class DealershipListSerializer(serializers.ModelSerializer):
    """Serializer for listing Dealerships."""

    country = CountryField(country_dict=True)
    admin_email = serializers.ReadOnlyField(source="admin.email")
    preferred_specs_count = serializers.SerializerMethodField()

    class Meta:
        model = Dealership
        fields = (
            "id",
            "name",
            "country",
            "city",
            "address",
            "balance",
            "admin_email",
            "preferred_specs_count",
            "created_at",
        )
        read_only_fields = ("balance", "preferred_specs_count")

    def get_preferred_specs_count(self, obj):
        return obj.preferred_specs.count()


class DealershipDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed Dealership view (including specs and admin info)."""

    country = CountryField(country_dict=True)
    admin_info = serializers.SerializerMethodField()
    preferred_specs = CarSpecificationSerializer(many=True, read_only=True)
    location = serializers.ReadOnlyField()

    class Meta:
        model = Dealership
        fields = (
            "id",
            "name",
            "country",
            "city",
            "address",
            "location",
            "balance",
            "admin",
            "admin_info",
            "preferred_specs",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("balance", "admin_info", "location", "preferred_specs")
        extra_kwargs = {"admin": {"write_only": True}}

    def get_admin_info(self, obj):
        if obj.admin:
            return {
                "id": obj.admin.id,
                "email": obj.admin.email,
                "is_active": obj.admin.is_active,
            }
        return None


class DealershipCarInventorySerializer(serializers.ModelSerializer):
    """Serializer for DealershipCarInventory (car stock)."""

    dealership_name = serializers.ReadOnlyField(source="dealership.name")
    car_model_name = serializers.ReadOnlyField(source="car_model.name")
    manufacturer = serializers.ReadOnlyField(source="car_model.manufacturer")

    class Meta:
        model = DealershipCarInventory
        fields = (
            "id",
            "dealership",
            "dealership_name",
            "car_model",
            "car_model_name",
            "manufacturer",
            "count",
            "purchase_price_avg",
            "updated_at",
        )
        read_only_fields = ("purchase_price_avg",)

        def validate(self, data):
            user = self.context["request"].user
            dealership = data.get("dealership") or (self.instance.dealership if self.instance else None)

            if not user.is_staff and dealership and dealership.admin != user:
                raise serializers.ValidationError(
                    "You must be the admin of this dealership or a staff user to manage inventory"
                )
            return data


class DealershipPreferredSupplierSerializer(serializers.ModelSerializer):
    """Serializer for DealershipPreferredSupplier (best supplier list)."""

    dealership_name = serializers.ReadOnlyField(source="dealership.name")
    car_model_full_name = serializers.ReadOnlyField(source="car_model.__str__")
    supplier_name = serializers.ReadOnlyField(source="supplier.name")

    class Meta:
        model = DealershipPreferredSupplier
        fields = (
            "id",
            "dealership",
            "dealership_name",
            "car_model",
            "car_model_full_name",
            "supplier",
            "supplier_name",
            "best_price",
            "last_checked",
        )
        read_only_fields = ("best_price", "last_checked")


class DealershipActionSerializer(serializers.ModelSerializer):
    """Serializer for DealershipAction (promotions/discounts)."""

    dealership_name = serializers.ReadOnlyField(source="dealership.name")
    car_models_count = serializers.SerializerMethodField()

    class Meta:
        model = DealershipAction
        fields = (
            "id",
            "dealership",
            "dealership_name",
            "name",
            "description",
            "start_date",
            "end_date",
            "discount_percentage",
            "car_models",
            "car_models_count",
            "created_at",
        )

    def get_car_models_count(self, obj):
        return obj.car_models.count()
