import unittest
from datetime import datetime, timezone

from ..serializers import (
    CarModelDetailSerializer,
    CarModelListCreateSerializer,
    CarSpecificationSerializer,
)


class MockCarSpecification:
    def __init__(
        self,
        id=1,
        engine_type="Electric",
        power_hp=200,
        color="Red",
        transmission="Auto",
        body_type="Sedan",
        is_active=True,
    ):
        self.id = id
        self.engine_type = engine_type
        self.power_hp = power_hp
        self.color = color
        self.transmission = transmission
        self.body_type = body_type
        self.is_active = is_active

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"{self.engine_type} / {self.power_hp}hp"


class MockCarModel:
    def __init__(self, id=10, name="Model 3", manufacturer="Tesla", base_specs=None, is_active=True):
        self.id = id
        self.name = name
        self.manufacturer = manufacturer
        self.base_specs = base_specs if base_specs is not None else MockCarSpecification()
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __str__(self):
        return f"{self.manufacturer} {self.name}"


class CarSpecificationSerializerTest(unittest.TestCase):
    def test_fields_contain_correct_data(self):
        """Test that serializer CarSpecificationSerializer contains the correct fields and data."""
        spec_instance = MockCarSpecification()
        serializer = CarSpecificationSerializer(instance=spec_instance)
        data = serializer.data

        expected_fields = ["id", "engine_type", "power_hp", "color", "transmission", "body_type", "is_active"]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["engine_type"], "Electric")
        self.assertEqual(data["power_hp"], 200)

    def test_validation_power_hp_is_integer(self):
        """Test that power_hp requires an integer number."""
        invalid_data = {
            "engine_type": "Diesel",
            "power_hp": "250hp",
            "color": "Black",
            "transmission": "Manual",
            "body_type": "SUV",
            "is_active": True,
        }
        serializer = CarSpecificationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("power_hp", serializer.errors)


class CarModelDetailSerializerTest(unittest.TestCase):
    def test_nested_specification_read_only(self):
        """Test that base_specs is nested and read-only."""
        spec = MockCarSpecification(power_hp=300)
        model_instance = MockCarModel(base_specs=spec)
        serializer = CarModelDetailSerializer(instance=model_instance)
        data = serializer.data

        self.assertIn("base_specs", data)
        self.assertIsInstance(data["base_specs"], dict)
        self.assertEqual(data["base_specs"]["power_hp"], 300)

        self.assertTrue(serializer.fields["created_at"].read_only)
        self.assertIn("created_at", data)


class CarModelListCreateSerializerTest(unittest.TestCase):
    def test_full_name_read_only_field(self):
        """Test that the full_name field is correctly calculated using __str__."""
        model_instance = MockCarModel(manufacturer="BMW", name="X5")
        serializer = CarModelListCreateSerializer(instance=model_instance)
        data = serializer.data

        self.assertIn("full_name", data)
        self.assertEqual(data["full_name"], "BMW X5")
        self.assertTrue(serializer.fields["full_name"].read_only)

    def test_base_specs_is_id_field(self):
        """Test that base_specs is used as a foreign key (ID)."""
        mock_data = {"name": "Focus", "manufacturer": "Ford", "base_specs": 99, "is_active": True}
        serializer = CarModelListCreateSerializer(data=mock_data)
        self.assertIn("base_specs", serializer.fields)
