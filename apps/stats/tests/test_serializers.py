import unittest
from decimal import Decimal

from apps.stats.serializers import (
    CustomerStatsSerializer,
    DealershipStatsSerializer,
    GlobalStatsSerializer,
    SupplierStatsSerializer,
)


class DealershipStatsSerializerTest(unittest.TestCase):

    def setUp(self):
        self.stats_data = {
            "dealership_id": 101,
            "dealership_name": "MegaCar Dealership",
            "total_cars_sold": 550,
            "total_revenue": Decimal("1500000.50"),
            "total_purchases": 400,
            "total_expenses": Decimal("1200000.25"),
            "net_profit": Decimal("300000.25"),
            "unique_customers": 350,
            "current_inventory_count": 150,
            "current_balance": Decimal("50000.00"),
            "active_promotions": 3,
        }

    def test_dealership_stats_fields(self):
        """Verify that the serializer correctly displays all fields."""
        serializer = DealershipStatsSerializer(self.stats_data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data

        expected_keys = [
            "dealership_id",
            "dealership_name",
            "total_cars_sold",
            "total_revenue",
            "total_purchases",
            "total_expenses",
            "net_profit",
            "unique_customers",
            "current_inventory_count",
            "current_balance",
            "active_promotions",
        ]
        self.assertEqual(set(data.keys()), set(expected_keys))

        self.assertEqual(data["dealership_id"], 101)
        self.assertEqual(data["dealership_name"], "MegaCar Dealership")
        self.assertEqual(data["total_cars_sold"], 550)
        self.assertEqual(data["total_revenue"], "1500000.50")
        self.assertEqual(data["net_profit"], "300000.25")
        self.assertEqual(data["active_promotions"], 3)


class CustomerStatsSerializerTest(unittest.TestCase):
    def setUp(self):
        self.stats_data = {
            "customer_id": 201,
            "customer_email": "jane.doe@example.com",
            "total_spent": Decimal("45000.00"),
            "total_purchases": 2,
            "current_balance": Decimal("1500.50"),
            "pending_offers": 1,
            "rejected_offers": 4,
            "favorite_car_model": "Ford Focus",
        }
        self.stats_data_null_model = self.stats_data.copy()
        self.stats_data_null_model["favorite_car_model"] = None

    def test_customer_stats_fields(self):
        """Verify that the serializer correctly displays all fields."""
        serializer = CustomerStatsSerializer(self.stats_data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data

        expected_keys = [
            "customer_id",
            "customer_email",
            "total_spent",
            "total_purchases",
            "current_balance",
            "pending_offers",
            "rejected_offers",
            "favorite_car_model",
        ]
        self.assertEqual(set(data.keys()), set(expected_keys))

        self.assertEqual(data["customer_email"], "jane.doe@example.com")
        self.assertEqual(data["total_spent"], "45000.00")
        self.assertEqual(data["pending_offers"], 1)
        self.assertEqual(data["favorite_car_model"], "Ford Focus")

    def test_favorite_car_model_null(self):
        """Verify that favorite_car_model correctly handles None."""
        serializer = CustomerStatsSerializer(self.stats_data_null_model)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data
        self.assertIsNone(data["favorite_car_model"])


class SupplierStatsSerializerTest(unittest.TestCase):

    def setUp(self):
        self.stats_data = {
            "supplier_id": 301,
            "supplier_name": "Global Parts Co.",
            "total_sales": 1200,
            "total_revenue": Decimal("500000.75"),
            "active_offers": 45,
            "total_stock": 2500,
            "partner_dealerships": 15,
            "active_promotions": 2,
        }

    def test_supplier_stats_fields(self):
        """Verify that the serializer correctly displays all fields."""
        serializer = SupplierStatsSerializer(self.stats_data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data

        expected_keys = [
            "supplier_id",
            "supplier_name",
            "total_sales",
            "total_revenue",
            "active_offers",
            "total_stock",
            "partner_dealerships",
            "active_promotions",
        ]
        self.assertEqual(set(data.keys()), set(expected_keys))

        self.assertEqual(data["supplier_name"], "Global Parts Co.")
        self.assertEqual(data["total_revenue"], "500000.75")
        self.assertEqual(data["active_offers"], 45)
        self.assertEqual(data["partner_dealerships"], 15)


class GlobalStatsSerializerTest(unittest.TestCase):

    def setUp(self):
        self.stats_data = {
            "total_dealerships": 5,
            "total_suppliers": 12,
            "total_customers": 500,
            "total_transactions": 3000,
            "total_transaction_volume": Decimal("5000000.00"),
            "total_cars_sold": 1500,
            "active_offers": 75,
            "most_popular_car_model": "Honda Civic",
            "most_popular_manufacturer": "Toyota",
        }
        self.stats_data_null_popularity = self.stats_data.copy()
        self.stats_data_null_popularity["most_popular_car_model"] = None
        self.stats_data_null_popularity["most_popular_manufacturer"] = None

    def test_global_stats_fields(self):
        """Verify that the serializer correctly displays all fields."""
        serializer = GlobalStatsSerializer(self.stats_data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data

        expected_keys = [
            "total_dealerships",
            "total_suppliers",
            "total_customers",
            "total_transactions",
            "total_transaction_volume",
            "total_cars_sold",
            "active_offers",
            "most_popular_car_model",
            "most_popular_manufacturer",
        ]
        self.assertEqual(set(data.keys()), set(expected_keys))

        self.assertEqual(data["total_dealerships"], 5)
        self.assertEqual(data["total_transaction_volume"], "5000000.00")
        self.assertEqual(data["most_popular_car_model"], "Honda Civic")
        self.assertEqual(data["most_popular_manufacturer"], "Toyota")

    def test_popularity_fields_null(self):
        """Verify that the popularity fields handle None values."""
        serializer = GlobalStatsSerializer(self.stats_data_null_popularity)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        data = serializer.data
        self.assertIsNone(data["most_popular_car_model"])
        self.assertIsNone(data["most_popular_manufacturer"])
