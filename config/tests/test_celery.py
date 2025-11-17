import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.dealerships.models import Dealership, DealershipAction, DealershipCarInventory
from apps.suppliers.models import Supplier, SupplierAction, SupplierCarOffer
from apps.transactions.models import Offer
from apps.users.models import CustomerProfile
from apps.vehicles.models import CarModel, CarSpecification

User = get_user_model()
specs_data = [
    {"engine_type": "Petrol", "power_hp": 150, "color": "Black", "transmission": "Manual", "body_type": "Sedan"},
    {"engine_type": "Diesel", "power_hp": 180, "color": "White", "transmission": "Automatic", "body_type": "SUV"},
    {"engine_type": "Electric", "power_hp": 300, "color": "Blue", "transmission": "Automatic", "body_type": "Sedan"},
    {"engine_type": "Hybrid", "power_hp": 200, "color": "Red", "transmission": "Automatic", "body_type": "Hatchback"},
]

specs = []
for spec_data in specs_data:
    spec, created = CarSpecification.objects.get_or_create(**spec_data)
    specs.append(spec)


models_data = [
    {"name": "Camry", "manufacturer": "Toyota", "base_specs": specs[0]},
    {"name": "X5", "manufacturer": "BMW", "base_specs": specs[1]},
    {"name": "Model 3", "manufacturer": "Tesla", "base_specs": specs[2]},
    {"name": "Prius", "manufacturer": "Toyota", "base_specs": specs[3]},
    {"name": "A4", "manufacturer": "Audi", "base_specs": specs[0]},
]

car_models = []
for model_data in models_data:
    car_model, created = CarModel.objects.get_or_create(
        name=model_data["name"],
        manufacturer=model_data["manufacturer"],
        defaults={"base_specs": model_data["base_specs"]},
    )
    car_models.append(car_model)

suppliers_data = [
    {"name": "Global Auto Supply", "year_founded": 2010, "info": "Leading supplier"},
    {"name": "Prime Motors Supply", "year_founded": 2015, "info": "Premium cars"},
    {"name": "Budget Auto Parts", "year_founded": 2018, "info": "Affordable options"},
]

suppliers = []
for supplier_data in suppliers_data:
    supplier, created = Supplier.objects.get_or_create(
        name=supplier_data["name"],
        defaults={"year_founded": supplier_data["year_founded"], "info": supplier_data["info"]},
    )
    suppliers.append(supplier)

for supplier in suppliers:
    for car_model in random.sample(car_models, 3):
        price = Decimal(random.randint(15000, 40000))
        stock = random.randint(5, 20)

        offer, created = SupplierCarOffer.objects.get_or_create(
            supplier=supplier, car_model=car_model, defaults={"price": price, "stock_count": stock}
        )

for supplier in suppliers[:2]:
    action, created = SupplierAction.objects.get_or_create(
        supplier=supplier,
        name=f"Special Offer {supplier.name}",
        defaults={
            "description": "Limited time discount",
            "start_date": timezone.now() - timezone.timedelta(days=1),
            "end_date": timezone.now() + timezone.timedelta(days=30),
            "discount_percentage": Decimal(random.randint(5, 15)),
        },
    )


for i in range(3):
    admin_email = f"dealer{i + 1}@test.com"
    admin, created = User.objects.get_or_create(
        email=admin_email,
        defaults={"password": "pbkdf2_sha256$870000$test", "is_dealership_admin": True, "email_confirmed": True},
    )

    if created:
        admin.set_password("Dealer123!")
        admin.save()

dealerships_data = [
    {"name": "Premium Motors NYC", "country": "US", "city": "New York", "balance": Decimal("150000")},
    {"name": "City Auto Sales", "country": "US", "city": "Los Angeles", "balance": Decimal("200000")},
    {"name": "Metro Car Center", "country": "US", "city": "Chicago", "balance": Decimal("100000")},
]

dealerships = []
for i, dealership_data in enumerate(dealerships_data):
    admin = User.objects.get(email=f"dealer{i + 1}@test.com")

    dealership, created = Dealership.objects.get_or_create(
        name=dealership_data["name"],
        defaults={
            "country": dealership_data["country"],
            "city": dealership_data["city"],
            "address": "123 Main St",
            "balance": dealership_data["balance"],
            "admin": admin,
        },
    )

    dealerships.append(dealership)

    if created:
        dealership.preferred_specs.add(*random.sample(specs, 2))

for dealership in dealerships:
    for car_model in random.sample(car_models, 2):
        inventory, created = DealershipCarInventory.objects.get_or_create(
            dealership=dealership,
            car_model=car_model,
            defaults={"count": random.randint(1, 5), "purchase_price_avg": Decimal(random.randint(18000, 38000))},
        )

for dealership in dealerships[:2]:
    action, created = DealershipAction.objects.get_or_create(
        dealership=dealership,
        name="Year-End Sale",
        defaults={
            "description": "Big discounts on selected models",
            "start_date": timezone.now() - timezone.timedelta(days=5),
            "end_date": timezone.now() + timezone.timedelta(days=25),
            "discount_percentage": Decimal(random.randint(10, 20)),
        },
    )

    if created:
        action.car_models.add(*random.sample(car_models, 2))

for i in range(5):
    customer_email = f"customer{i + 1}@test.com"
    customer_user, created = User.objects.get_or_create(
        email=customer_email,
        defaults={
            "password": "pbkdf2_sha256$870000$test",
            "is_customer": True,
            "email_confirmed": True,
            "first_name": f"Customer{i + 1}",
        },
    )

    if created:
        customer_user.set_password("Customer123!")
        customer_user.save()

        profile = CustomerProfile.objects.create(user=customer_user, balance=Decimal(random.randint(30000, 100000)))

customers = CustomerProfile.objects.filter(is_active=True)

for customer in customers[:3]:
    car_model = random.choice(car_models)
    max_price = Decimal(random.randint(25000, 45000))

    offer, created = Offer.objects.get_or_create(
        customer=customer, car_model=car_model, defaults={"max_price": max_price, "status": "PENDING"}
    )
