from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from django_countries.fields import Country
from rest_framework import serializers


class MockUser:
    def __init__(
        self,
        id=1,
        email="test@admin.com",
        is_staff=False,
        is_superuser=False,
        is_authenticated=True,
        is_dealership_admin=False,
    ):
        self.id = id
        self.email = email
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.is_authenticated = is_authenticated
        self.is_dealership_admin = is_dealership_admin

    @property
    def pk(self):
        return self.id


class MockCarSpecification:
    def __init__(self, id=1, name="Luxury"):
        self.id = id
        self.name = name

    @property
    def pk(self):
        return self.id


class MockCarModel:
    def __init__(self, id=5, name="Model S", manufacturer="Tesla"):
        self.id = id
        self.name = name
        self.manufacturer = manufacturer

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"{self.manufacturer} - {self.name}"


class MockSupplier:
    def __init__(self, id=20, name="PartsGlobal"):
        self.id = id
        self.name = name

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return self.name


class MockDealership:
    def __init__(self, id=10, name="AutoHub", admin=None, balance=Decimal("100000.00"), country_code="US", city="NY"):
        self.id = id
        self.name = name
        self.country = Country(country_code)
        self.city = city
        self.address = "123 Main St"
        self.balance = balance
        self.admin = admin if admin is not None else MockUser(id=2, email="dealer@admin.com")
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        self.preferred_specs = MagicMock()
        self.location = f"{self.city}, {self.country.name}"

    @property
    def pk(self):
        return self.id


class MockDealershipCarInventory:
    def __init__(self, id=100, dealership=None, car_model=None, count=5, price=Decimal("10000.00")):
        self.id = id
        self.dealership = dealership if dealership is not None else MockDealership()
        self.car_model = car_model if car_model is not None else MockCarModel()
        self.count = count
        self.purchase_price_avg = price
        self.updated_at = datetime.now(timezone.utc)

    @property
    def pk(self):
        return self.id


class MockDealershipPreferredSupplier:
    def __init__(self, id=200, dealership=None, car_model=None, supplier=None, price=Decimal("9500.00")):
        self.id = id
        self.dealership = dealership if dealership is not None else MockDealership()
        self.car_model = car_model if car_model is not None else MockCarModel()
        self.supplier = supplier if supplier is not None else MockSupplier()
        self.best_price = price
        self.last_checked = datetime.now(timezone.utc)

    @property
    def pk(self):
        return self.id


class MockDealershipAction:
    def __init__(self, id=300, dealership=None, name="Xmas Sale", discount=Decimal("10.00")):
        self.id = id
        self.dealership = dealership if dealership is not None else MockDealership()
        self.name = name
        self.description = "Holiday discount"
        self.start_date = datetime.now(timezone.utc) - timedelta(days=1)
        self.end_date = datetime.now(timezone.utc) + timedelta(days=7)
        self.discount_percentage = discount

        self.car_models = MagicMock()
        self.car_models.count.return_value = 3

    @property
    def pk(self):
        return self.id


class MockSupplierCarOffer:
    def __init__(self, id=10, supplier=None, car_model=None, price=Decimal("1500.00"), stock_count=5, is_active=True):
        self.id = id
        self.supplier = supplier if supplier is not None else MockSupplier()
        self.car_model = car_model if car_model is not None else MockCarModel()
        self.price = price
        self.stock_count = stock_count
        self.is_active = is_active

    @property
    def pk(self):
        return self.id


class MockSupplierAction:
    def __init__(self, id=20, supplier=None, name="Summer Sale", discount_percentage=Decimal("10.00"), is_active=True):
        self.id = id
        self.supplier = supplier if supplier is not None else MockSupplier()
        self.name = name
        self.description = "10% off selected parts."
        self.start_date = datetime.now(timezone.utc)
        self.end_date = datetime.now(timezone.utc)
        self.discount_percentage = discount_percentage
        self.is_active = is_active

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"{self.supplier.name} - {self.name}"


class MockRelatedField(serializers.Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value.pk if hasattr(value, "pk") else value


class MockCustomerProfile:
    def __init__(self, user=None, balance=Decimal("1000.00")):
        self.id = 10
        self.user = user if user is not None else MockUser()
        self.balance = balance

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"Customer Profile ID: {self.id}"


class MockOffer:
    def __init__(
        self,
        id=100,
        car_model=None,
        max_price=Decimal("500.00"),
        status="PENDING",
        dealership_match=None,
        customer=None,
    ):
        self.id = id
        self.car_model = car_model if car_model is not None else MockCarModel()
        self.max_price = max_price
        self.status = status
        self.dealership_match = dealership_match if dealership_match is not None else MockDealership()
        self.customer = customer if customer is not None else MockCustomerProfile()
        self.created_at = datetime.now(timezone.utc)

    @property
    def pk(self):
        return self.id


class MockTransaction:
    def __init__(
        self,
        id=200,
        transaction_type="SALE",
        amount=Decimal("25000.00"),
        car_model=None,
        count=1,
        sender=None,
        recipient=None,
    ):
        self.id = id
        self.transaction_type = transaction_type
        self.amount = amount
        self.car_model = car_model if car_model is not None else MockCarModel()
        self.count = count
        self.sender = sender if sender is not None else MockCustomerProfile()
        self.recipient = recipient if recipient is not None else MockDealership()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @property
    def pk(self):
        return self.id

    def __str__(self):
        return f"{self.transaction_type} {self.id} - {self.amount} USD"
