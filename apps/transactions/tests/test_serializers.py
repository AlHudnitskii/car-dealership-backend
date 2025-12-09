import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.transactions.serializers import (
    OfferCreateSerializer,
    OfferListSerializer,
    TransactionSerializer,
)

from ....mocks import (
    MockCarModel,
    MockCustomerProfile,
    MockDealership,
    MockOffer,
    MockRelatedField,
    MockTransaction,
    MockUser,
)


class OfferCreateSerializerTest(unittest.TestCase):
    class MockedOfferCreateSerializer(OfferCreateSerializer):
        car_model = MockRelatedField()

    def setUp(self):
        self.mock_user = MockUser(is_customer=True)
        self.mock_user.customer_profile.balance = Decimal("10000.00")

        self.mock_request = MagicMock()
        self.mock_request.user = self.mock_user

        self.valid_data = {"car_model": 5, "max_price": Decimal("5000.00")}

    def get_serializer(self, data=None):
        return self.MockedOfferCreateSerializer(data=data, context={"request": self.mock_request})

    def test_valid_offer_creation(self):
        """Test that validation passes with a customer and sufficient balance."""
        serializer = self.get_serializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        self.assertNotIn("status", serializer.validated_data)
        self.assertNotIn("dealership_match", serializer.validated_data)

    def test_validation_not_a_customer(self):
        """Test validation fails if the user is not a customer."""
        self.mock_user.is_customer = False

        serializer = self.get_serializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())

        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(str(serializer.errors["non_field_errors"][0]), "Only customers can create Offers.")

    def test_validation_insufficient_balance(self):
        """Test validation fails if max_price exceeds customer balance."""
        self.mock_user.customer_profile.balance = Decimal("100.00")

        serializer = self.get_serializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())

        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(str(serializer.errors["non_field_errors"][0]), "Insufficient balance for this offer.")

    @patch("apps.transactions.models.Offer.objects.create")
    def test_create_method_passes_customer_profile(self, mock_create):
        """Test that the create method uses the customer profile from context."""

        serializer = self.get_serializer(data=self.valid_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        serializer.create(validated_data)
        mock_create.assert_called_once()
        call_args, call_kwargs = mock_create.call_args

        self.assertEqual(call_kwargs["customer"], self.mock_user.customer_profile)
        self.assertEqual(call_kwargs["max_price"], Decimal("5000.00"))
        self.assertEqual(call_kwargs["car_model"], 5)


class OfferListSerializerTest(unittest.TestCase):
    def test_offer_list_fields_and_email_source(self):
        """Test that all required fields are present, including the nested email source."""

        mock_user = MockUser(email="customer@mail.com")
        mock_profile = MockCustomerProfile(user=mock_user)
        offer_instance = MockOffer(customer=mock_profile, max_price=Decimal("15000.00"), status="MATCHED")

        serializer = OfferListSerializer(instance=offer_instance)
        data = serializer.data

        expected_fields = ["id", "car_model", "max_price", "status", "dealership_match", "customer_email", "created_at"]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["customer_email"], "customer@mail.com")
        self.assertEqual(data["status"], "MATCHED")


class TransactionSerializerTest(unittest.TestCase):
    def setUp(self):
        self.mock_car = MockCarModel(name="Civic")
        self.mock_sender = MockCustomerProfile()
        self.mock_recipient = MockDealership()

        self.transaction_instance = MockTransaction(
            transaction_type="SALE",
            amount=Decimal("20000.00"),
            car_model=self.mock_car,
            sender=self.mock_sender,
            recipient=self.mock_recipient,
        )

    def test_transaction_fields_and_read_only(self):
        """Test that all fields are present and correctly marked as read_only."""
        serializer = TransactionSerializer(instance=self.transaction_instance)
        data = serializer.data

        expected_fields = [
            "id",
            "transaction_type",
            "amount",
            "car_model",
            "car_model_name",
            "count",
            "sender_representation",
            "recipient_representation",
            "created_at",
            "updated_at",
        ]

        self.assertEqual(list(data.keys()), expected_fields)
        self.assertEqual(data["transaction_type"], "SALE")
        self.assertEqual(data["amount"], "20000.00")

        for field_name in expected_fields:
            self.assertTrue(serializer.fields[field_name].read_only)

    def test_representation_fields(self):
        """Test that representation fields correctly use the __str__ method of mock objects."""
        serializer = TransactionSerializer(instance=self.transaction_instance)
        data = serializer.data

        self.assertEqual(data["car_model_name"], "CarModel: Civic")
        self.assertEqual(data["sender_representation"], str(self.mock_sender))
        self.assertEqual(data["recipient_representation"], str(self.mock_recipient))
