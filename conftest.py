import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from faker import Faker
from rest_framework.test import APIClient

from apps.dealerships.models import Dealership, DealershipAction
from apps.suppliers.models import Supplier, SupplierAction, SupplierCarOffer
from apps.transactions.models import Offer, Transaction
from apps.users.models import CustomerProfile
from apps.vehicles.models import CarModel, CarSpecification

User = get_user_model()
fake = Faker()


# ========== Clients ==========


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory fixture for creating users with different roles."""

    def _create_user(
        email=None,
        password="testpass123",
        is_customer=False,
        is_dealership_admin=False,
        is_supplier_admin=False,
        is_staff=False,
        is_superuser=False,
        email_confirmed=False,
        **kwargs,
    ):
        if email is None:
            email = fake.email()

        user = User.objects.create_user(
            email=email,
            password=password,
            is_customer=is_customer,
            is_dealership_admin=is_dealership_admin,
            is_supplier_admin=is_supplier_admin,
            is_staff=is_staff,
            is_superuser=is_superuser,
            email_confirmed=email_confirmed,
            **kwargs,
        )
        return user

    return _create_user


@pytest.fixture
def regular_user(create_user):
    """Create a regular customer user."""
    return create_user(email="regular@test.com", is_customer=True, email_confirmed=True)


@pytest.fixture
def regular_user_confirmed(create_user):
    """Create a confirmed regular customer user."""
    return create_user(email="confirmed@test.com", is_customer=True, email_confirmed=True)


@pytest.fixture
def other_user(create_user):
    """Create another user for testing."""
    return create_user(email="other@test.com", is_customer=True, username="otheruser")


@pytest.fixture
def superuser(create_user):
    """Create a superuser."""
    return create_user(email="admin@test.com", is_superuser=True, is_staff=True)


@pytest.fixture
def dealership_admin(create_user):
    """Create a dealership admin user."""
    return create_user(email="dealer@test.com", is_dealership_admin=True)


@pytest.fixture
def supplier_admin(create_user):
    """Create a supplier admin user."""
    return create_user(email="supplier@test.com", is_supplier_admin=True)


@pytest.fixture
def regular_client(api_client, regular_user):
    """Return an authenticated API client for regular user."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def auth_client(api_client, dealership_admin):
    """Return an authenticated API client for dealership admin."""
    api_client.force_authenticate(user=dealership_admin)
    return api_client


@pytest.fixture
def superuser_client(api_client, superuser):
    """Return an authenticated API client for superuser."""
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def supplier_auth_client(api_client, supplier_admin):
    """Return an authenticated API client for supplier admin."""
    api_client.force_authenticate(user=supplier_admin)
    return api_client


# ========== Vehicle-related fixtures ==========


@pytest.fixture
def car_specification(db):
    """Create a car specification."""
    return CarSpecification.objects.create(
        engine_type="Petrol",
        power_hp=200,
        color="Black",
        transmission="Automatic",
        body_type="Sedan",
    )


@pytest.fixture
def spec_data():
    """Return data for creating a car specification."""
    return {
        "engine_type": "Electric",
        "power_hp": 350,
        "color": "White",
        "transmission": "Automatic",
        "body_type": "SUV",
    }


@pytest.fixture
def car_model(db, car_specification):
    """Create a car model."""
    return CarModel.objects.create(
        name="A4",
        manufacturer="Audi",
        base_specs=car_specification,
    )


# ========== Supplier-related fixtures ==========


@pytest.fixture
def supplier_instance(db):
    """Create a supplier instance."""
    return Supplier.objects.create(
        name="Global Auto Supplier",
        year_founded=2000,
        info="Leading car supplier",
    )


@pytest.fixture
def test_supplier(db):
    """Create a test supplier."""
    return Supplier.objects.create(
        name="Test Supplier Inc",
        year_founded=2010,
        info="Test supplier",
    )


@pytest.fixture
def supplier_car_offer(db, supplier_instance, car_model):
    """Create a supplier car offer."""
    return SupplierCarOffer.objects.create(
        supplier=supplier_instance,
        car_model=car_model,
        price=20000.00,
        stock_count=10,
    )


@pytest.fixture
def supplier_action(db, supplier_instance):
    """Create a supplier action/promotion."""
    return SupplierAction.objects.create(
        supplier=supplier_instance,
        name="Summer Sale",
        description="Big summer discount",
        start_date=fake.past_datetime(),
        end_date=fake.future_datetime(),
        discount_percentage=10.00,
    )


# ========== Dealership-related fixtures ==========


@pytest.fixture
def dealership_instance(db, dealership_admin):
    """Create a dealership instance."""
    return Dealership.objects.create(
        name="Premium Motors",
        country="US",
        city="New York",
        address="123 Main St",
        balance=100000.00,
        admin=dealership_admin,
    )


@pytest.fixture
def dealership_action(db, dealership_instance, car_model):
    """Create a dealership action/promotion."""
    action = DealershipAction.objects.create(
        dealership=dealership_instance,
        name="New Year Sale",
        description="Special new year discount",
        start_date=fake.past_datetime(),
        end_date=fake.future_datetime(),
        discount_percentage=15.00,
    )
    action.car_models.add(car_model)
    return action


# ========== Customer-related fixtures ==========


@pytest.fixture
def customer_profile(db, regular_user):
    """Create a customer profile."""
    return CustomerProfile.objects.get_or_create(
        user=regular_user,
        defaults={"balance": 10000.00},
    )[0]


@pytest.fixture
def customer_profile_instance(db, regular_user):
    """Create a customer profile instance."""
    profile, _ = CustomerProfile.objects.get_or_create(
        user=regular_user,
        defaults={"balance": 50000.00},
    )
    return profile


@pytest.fixture
def test_customer_profile(db, regular_user):
    """Create a test customer profile."""
    profile, _ = CustomerProfile.objects.get_or_create(
        user=regular_user,
        defaults={"balance": 75000.00},
    )
    return profile


# ========== Transaction-related fixtures ==========


@pytest.fixture
def offer_instance(db, customer_profile, car_model):
    """Create an offer instance."""
    return Offer.objects.create(
        customer=customer_profile,
        car_model=car_model,
        max_price=30000.00,
        status="PENDING",
    )


@pytest.fixture
def transaction_instance(db, dealership_instance, customer_profile, car_model):
    """Create a transaction instance."""
    dealership_ct = ContentType.objects.get_for_model(Dealership)
    customer_ct = ContentType.objects.get_for_model(CustomerProfile)

    return Transaction.objects.create(
        transaction_type="SALE",
        amount=25000.00,
        car_model=car_model,
        count=1,
        sender_content_type=dealership_ct,
        sender_object_id=dealership_instance.pk,
        recipient_content_type=customer_ct,
        recipient_object_id=customer_profile.pk,
    )


@pytest.fixture
def setup_dealership_transactions(db, dealership_instance, test_supplier, test_customer_profile, car_model):
    """
    Set up a complete transaction scenario:
    - Dealership purchases from supplier
    - Dealership sells to customer
    - Create pending and rejected offers
    """
    dealership_ct = ContentType.objects.get_for_model(Dealership)
    customer_ct = ContentType.objects.get_for_model(CustomerProfile)
    supplier_ct = ContentType.objects.get_for_model(Supplier)

    Transaction.objects.create(
        transaction_type="PURCHASE",
        amount=15000.00,
        car_model=car_model,
        count=1,
        sender_content_type=supplier_ct,
        sender_object_id=test_supplier.pk,
        recipient_content_type=dealership_ct,
        recipient_object_id=dealership_instance.pk,
    )

    Transaction.objects.create(
        transaction_type="SALE",
        amount=25000.00,
        car_model=car_model,
        count=1,
        sender_content_type=dealership_ct,
        sender_object_id=dealership_instance.pk,
        recipient_content_type=customer_ct,
        recipient_object_id=test_customer_profile.pk,
    )

    Offer.objects.create(
        customer=test_customer_profile,
        car_model=car_model,
        max_price=30000.00,
        status="PENDING",
    )

    Offer.objects.create(
        customer=test_customer_profile,
        car_model=car_model,
        max_price=20000.00,
        status="REJECTED",
    )

    return {
        "dealership": dealership_instance,
        "supplier": test_supplier,
        "customer": test_customer_profile,
        "car_model": car_model,
    }
