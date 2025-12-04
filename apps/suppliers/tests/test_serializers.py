import unittest
from decimal import Decimal

from apps.suppliers.serializers import (
    SupplierActionSerializer,
    SupplierCarOfferListSerializer,
    SupplierCarOfferManageSerializer,
    SupplierSerializer,
)

from ....mocks import MockCarModel, MockRelatedField, MockSupplier, MockSupplierAction, MockSupplierCarOffer


class SupplierSerializerTest(unittest.TestCase):
    def test_supplier_fields_and_read_only(self):
        """Test fields representation and read-only status."""
        supplier_instance = MockSupplier()
        supplier_instance.car_offers.filter.return_value.count.return_value = 15

        serializer = SupplierSerializer(instance=supplier_instance)
        data = serializer.data

        expected_fields = ["id", "name", "year_founded", "info", "is_active", "created_at", "active_offers_count"]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["active_offers_count"], 15)

        self.assertTrue(serializer.fields["active_offers_count"].read_only)
        self.assertFalse(serializer.fields["name"].read_only)

    def test_get_active_offers_count_method(self):
        """Test the logic inside get_active_offers_count uses correct filter."""
        supplier_instance = MockSupplier()
        serializer = SupplierSerializer(instance=supplier_instance)

        serializer.get_active_offers_count(supplier_instance)
        supplier_instance.car_offers.filter.assert_called_with(is_active=True)


class SupplierCarOfferListSerializerTest(unittest.TestCase):
    def setUp(self):
        self.mock_supplier = MockSupplier(name="Best Wheels Inc.")
        self.mock_car_model = MockCarModel(name="Model Y")
        self.offer_instance = MockSupplierCarOffer(
            supplier=self.mock_supplier, car_model=self.mock_car_model, price=Decimal("45000.00")
        )

    def test_read_only_fields_representation(self):
        """Test that ReadOnlyFields correctly pull nested data."""
        serializer = SupplierCarOfferListSerializer(instance=self.offer_instance)
        data = serializer.data

        self.assertEqual(data["supplier_name"], "Best Wheels Inc.")
        self.assertEqual(data["car_model_full_name"], "Ford - Model Y")

    def test_field_inclusion(self):
        """Test that all required fields for listing are included."""
        serializer = SupplierCarOfferListSerializer(instance=self.offer_instance)
        data = serializer.data

        expected_fields = [
            "id",
            "supplier",
            "supplier_name",
            "car_model",
            "car_model_full_name",
            "price",
            "stock_count",
            "is_active",
        ]
        self.assertEqual(list(data.keys()), expected_fields)

        self.assertEqual(data["supplier"], self.mock_supplier.id)
        self.assertEqual(data["car_model"], self.mock_car_model.id)


class SupplierCarOfferManageSerializerTest(unittest.TestCase):
    class MockedSupplierCarOfferManageSerializer(SupplierCarOfferManageSerializer):
        supplier = MockRelatedField()
        car_model = MockRelatedField()

    def setUp(self):
        self.valid_data = {
            "supplier": 1,
            "car_model": 5,
            "price": Decimal("1250.99"),
            "stock_count": 10,
            "is_active": True,
        }

    def get_serializer(self, data=None, instance=None):
        return self.MockedSupplierCarOfferManageSerializer(instance=instance, data=data)

    def test_writable_fields(self):
        """Test that fields are writable for CUD operations."""
        serializer = self.get_serializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        validated_data = serializer.validated_data

        self.assertIn("price", validated_data)
        self.assertIn("stock_count", validated_data)
        self.assertFalse(serializer.fields["price"].read_only)
        self.assertFalse(serializer.fields["stock_count"].read_only)


class SupplierActionSerializerTest(unittest.TestCase):
    def setUp(self):
        self.mock_supplier = MockSupplier(name="Parts Master")
        self.action_instance = MockSupplierAction(
            supplier=self.mock_supplier, name="Winter Tires Deal", discount_percentage=Decimal("15.50")
        )

    def test_supplier_name_read_only_field(self):
        """Test the ReadOnlyField for supplier_name."""
        serializer = SupplierActionSerializer(instance=self.action_instance)
        data = serializer.data

        self.assertEqual(data["supplier_name"], "Parts Master")

    def test_required_fields(self):
        """Test that all required fields are included."""
        serializer = SupplierActionSerializer(instance=self.action_instance)
        data = serializer.data

        expected_fields = [
            "id",
            "supplier",
            "supplier_name",
            "name",
            "description",
            "start_date",
            "end_date",
            "discount_percentage",
            "is_active",
        ]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["discount_percentage"], "15.50")
