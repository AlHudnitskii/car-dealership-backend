import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from rest_framework import permissions

from apps.dealerships.permissions import IsDealershipOwner, IsDealershipStaff, OrPermission
from apps.dealerships.serializers import (
    DealershipCarInventorySerializer,
    DealershipListSerializer,
    DealershipPreferredSupplierSerializer,
)

from ....mocks import (
    MockCarModel,
    MockDealership,
    MockDealershipCarInventory,
    MockDealershipPreferredSupplier,
    MockSupplier,
    MockUser,
)


class DealershipListSerializerTest(unittest.TestCase):
    def setUp(self):
        self.admin = MockUser(id=5, email="test@list.com")
        self.dealership = MockDealership(admin=self.admin, balance=Decimal("50000.55"), country_code="CA")
        self.dealership.preferred_specs.count.return_value = 5

    def test_fields_and_representation(self):
        """Test field inclusion and ReadOnly/SerializerMethodField output."""
        serializer = DealershipListSerializer(instance=self.dealership)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "country",
            "city",
            "address",
            "balance",
            "admin_email",
            "preferred_specs_count",
            "created_at",
        ]
        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["name"], "AutoHub")
        self.assertEqual(data["admin_email"], "test@list.com")
        self.assertEqual(data["preferred_specs_count"], 5)
        self.assertEqual(data["country"]["name"], "Canada")

    def test_read_only_fields(self):
        """Test that balance and preferred_specs_count are read-only."""
        serializer = DealershipListSerializer()
        self.assertTrue(serializer.fields["balance"].read_only)
        self.assertTrue(serializer.fields["preferred_specs_count"].read_only)


class DealershipCarInventorySerializerTest(unittest.TestCase):
    def setUp(self):
        self.dealer_admin = MockUser(id=5, email="dealer@inv.com", is_dealership_admin=True)
        self.dealership = MockDealership(admin=self.dealer_admin, name="InvDealership")
        self.car_model = MockCarModel(name="F-150", manufacturer="Ford")
        self.inventory = MockDealershipCarInventory(dealership=self.dealership, car_model=self.car_model, count=10)

        self.mock_request = MagicMock()
        self.mock_request.user = self.dealer_admin
        self.context = {"request": self.mock_request}

    def test_read_only_fields(self):
        """Test ReadOnlyFields for nested model data."""
        serializer = DealershipCarInventorySerializer(instance=self.inventory)
        data = serializer.data

        self.assertEqual(data["dealership_name"], "InvDealership")
        self.assertEqual(data["car_model_name"], "F-150")
        self.assertEqual(data["manufacturer"], "Ford")
        self.assertEqual(data["count"], 10)
        self.assertTrue(serializer.fields["purchase_price_avg"].read_only)


class DealershipPreferredSupplierSerializerTest(unittest.TestCase):
    def setUp(self):
        self.dealership = MockDealership(name="PriceFinder")
        self.car_model = MockCarModel(name="Prius", manufacturer="Toyota")
        self.supplier = MockSupplier(name="JDM Supply")
        self.pref_supplier = MockDealershipPreferredSupplier(
            dealership=self.dealership, car_model=self.car_model, supplier=self.supplier, price=Decimal("18000.99")
        )

    def test_read_only_fields_representation(self):
        """Test ReadOnlyFields for nested model data and __str__ method."""
        serializer = DealershipPreferredSupplierSerializer(instance=self.pref_supplier)
        data = serializer.data

        self.assertEqual(data["dealership_name"], "PriceFinder")
        self.assertEqual(data["supplier_name"], "JDM Supply")

        self.assertEqual(data["car_model_full_name"], "Toyota - Prius")
        self.assertEqual(data["best_price"], "18000.99")

        self.assertTrue(serializer.fields["best_price"].read_only)
        self.assertTrue(serializer.fields["last_checked"].read_only)


class IsDealershipOwnerTest(unittest.TestCase):
    def setUp(self):
        self.owner = MockUser(id=1, email="owner@d.com")
        self.other_user = MockUser(id=2, email="other@d.com")
        self.dealership = MockDealership(admin=self.owner)
        self.permission = IsDealershipOwner()

    def test_safe_methods_allowed(self):
        """Test SAFE_METHODS (GET, HEAD, OPTIONS) are allowed for any user."""
        mock_request = MagicMock(method="GET", user=self.other_user)
        self.assertTrue(self.permission.has_object_permission(mock_request, None, self.dealership))

    def test_owner_allowed_unsafe_methods(self):
        """Test unsafe methods (POST, PUT, DELETE) are allowed for the owner."""
        mock_request = MagicMock(method="PUT", user=self.owner)
        self.assertTrue(self.permission.has_object_permission(mock_request, None, self.dealership))

    def test_other_user_denied_unsafe_methods(self):
        """Test unsafe methods are denied for non-owner users."""
        mock_request = MagicMock(method="POST", user=self.other_user)
        self.assertFalse(self.permission.has_object_permission(mock_request, None, self.dealership))


class IsDealershipStaffTest(unittest.TestCase):
    def setUp(self):
        self.staff_user = MockUser(is_dealership_admin=True)
        self.normal_user = MockUser(is_dealership_admin=False)
        self.permission = IsDealershipStaff()

    def test_staff_allowed(self):
        """Test that user with is_dealership_admin=True has permission."""
        mock_request = MagicMock(user=self.staff_user)
        self.assertTrue(self.permission.has_permission(mock_request, None))

    def test_normal_user_denied(self):
        """Test that a regular authenticated user is denied."""
        mock_request = MagicMock(user=self.normal_user)
        self.assertFalse(self.permission.has_permission(mock_request, None))

    def test_unauthenticated_user_denied(self):
        """Test that an unauthenticated user is denied."""
        unauth_user = MockUser(is_authenticated=False)
        mock_request = MagicMock(user=unauth_user)
        self.assertFalse(self.permission.has_permission(mock_request, None))


class OrPermissionTest(unittest.TestCase):
    def setUp(self):
        class MockPermA(permissions.BasePermission):
            def has_permission(self, request, view):
                return request.user.role == "A"

            def has_object_permission(self, request, view, obj):
                return obj.pk == 100

        class MockPermB(permissions.BasePermission):
            def has_permission(self, request, view):
                return request.user.role == "B"

            def has_object_permission(self, request, view, obj):
                return obj.pk == 200

        self.MockPermA = MockPermA
        self.MockPermB = MockPermB
        self.mock_obj_100 = MagicMock(pk=100)
        self.mock_obj_200 = MagicMock(pk=200)

    def test_has_permission_a_granted(self):
        """Test has_permission granted if the first permission is true."""
        permission = OrPermission(self.MockPermA, self.MockPermB)
        mock_request = MagicMock(user=MagicMock(role="A"))
        self.assertTrue(permission.has_permission(mock_request, None))

    def test_has_permission_b_granted(self):
        """Test has_permission granted if the second permission is true."""
        permission = OrPermission(self.MockPermA, self.MockPermB)
        mock_request = MagicMock(user=MagicMock(role="B"))
        self.assertTrue(permission.has_permission(mock_request, None))

    def test_has_permission_denied(self):
        """Test has_permission denied if neither permission is true."""
        permission = OrPermission(self.MockPermA, self.MockPermB)
        mock_request = MagicMock(user=MagicMock(role="C"))
        self.assertFalse(permission.has_permission(mock_request, None))

    def test_has_object_permission_a_granted(self):
        """Test has_object_permission granted if the first permission is true."""
        permission = OrPermission(self.MockPermA, self.MockPermB)
        mock_request = MagicMock(user=MagicMock(role="C"))
        self.assertTrue(permission.has_object_permission(mock_request, None, self.mock_obj_100))

    def test_has_object_permission_denied(self):
        """Test has_object_permission denied if neither object permission is true."""
        permission = OrPermission(self.MockPermA, self.MockPermB)
        mock_request = MagicMock(user=MagicMock(role="C"))
        self.assertFalse(permission.has_object_permission(mock_request, None, MagicMock(pk=300)))
