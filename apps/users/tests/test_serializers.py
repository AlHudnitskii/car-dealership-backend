import unittest
from datetime import datetime, timezone

from apps.users.serializers import (
    CustomerProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class MockUser:
    def __init__(
        self,
        id=1,
        email="test@example.com",
        username="tester",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_superuser=False,
        is_staff=False,
        is_customer=True,
        is_dealership_admin=False,
        is_supplier_admin=False,
        email_confirmed=False,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        self.is_customer = is_customer
        self.is_dealership_admin = is_dealership_admin
        self.is_supplier_admin = is_supplier_admin
        self.email_confirmed = email_confirmed
        self.date_joined = datetime.now(timezone.utc)
        self.password = "hashed_password"

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return self.email


class MockCustomerProfile:
    def __init__(self, id=10, user=None, balance="100.50", auto_generated_info=None):
        self.id = id
        self.user = user if user is not None else MockUser()
        self.balance = balance
        self.auto_generated_info = auto_generated_info if auto_generated_info is not None else {"last_login": "today"}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"Profile of {self.user.email}"


class UserSerializerTest(unittest.TestCase):
    def test_user_fields_contain_correct_data(self):
        """Test that the UserSerializer correctly displays all general fields."""
        user_instance = MockUser(email="admin@site.com", is_staff=True, is_superuser=True)
        serializer = UserSerializer(instance=user_instance)
        data = serializer.data

        expected_fields = [
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
        ]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertTrue(data["is_superuser"])
        self.assertEqual(data["email"], "admin@site.com")

    def test_read_only_fields(self):
        """Test that email_confirmed and date_joined are read-only."""
        serializer = UserSerializer()
        self.assertTrue(serializer.fields["email_confirmed"].read_only)
        self.assertTrue(serializer.fields["date_joined"].read_only)


class UserRegistrationSerializerTest(unittest.TestCase):
    def test_required_fields_validation(self):
        """Test that registration requires email and password."""
        invalid_data = {"first_name": "Test", "last_name": "User"}
        serializer = UserRegistrationSerializer(data=invalid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("password", serializer.errors)

    def test_password_is_write_only(self):
        """Test that the password field is write_only and not returned in the output."""
        serializer = UserRegistrationSerializer()

        self.assertTrue(serializer.fields["password"].write_only)
        self.assertEqual(serializer.fields["password"].style.get("input_type"), "password")

        user_instance = MockUser()
        serializer = UserRegistrationSerializer(instance=user_instance)
        self.assertNotIn("password", serializer.data)


class CustomerProfileSerializerTest(unittest.TestCase):
    def setUp(self):
        self.mock_user = MockUser(first_name="Alex", last_name="Customer")
        self.mock_profile = MockCustomerProfile(
            user=self.mock_user, balance="5000.75", auto_generated_info={"city": "New York"}
        )

    def test_nested_user_details(self):
        """Test that user_details is nested and shows the correct attributes."""
        serializer = CustomerProfileSerializer(instance=self.mock_profile)
        data = serializer.data

        self.assertIn("user_details", data)
        self.assertIsInstance(data["user_details"], dict)
        self.assertEqual(data["user_details"]["first_name"], "Alex")

        self.assertIn("is_superuser", data["user_details"])

    def test_read_only_fields(self):
        """Test that user, balance, and auto_generated_info are read-only."""
        serializer = CustomerProfileSerializer()

        self.assertTrue(serializer.fields["user"].read_only)
        self.assertTrue(serializer.fields["balance"].read_only)
        self.assertTrue(serializer.fields["auto_generated_info"].read_only)

    def test_user_field_representation(self):
        """Test that the 'user' field (a ForeignKey) returns the User's primary key (ID)."""
        serializer = CustomerProfileSerializer(instance=self.mock_profile)
        data = serializer.data

        self.assertEqual(data["user"], self.mock_user.id)
