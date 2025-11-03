from django.db import models
from suppliers.models import Supplier
from users.models import User
from vehicles.models import CarModel, CarSpecification

from config.models import BaseModel


class Dealership(BaseModel):
    """Dealership model."""

    name = models.CharField(max_length=255, unique=True)
    # Without PostGIS
    location = models.CharField(max_length=255, verbose_name="Location (city, address)")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    admin = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name="managed_dealership")
    preferred_specs = models.ManyToManyField(CarSpecification, related_name="preferred_by_dealerships", blank=True)

    def __str__(self):
        return self.name


class DealershipCarInventory(BaseModel):
    """The stock of cars and their number in the showroom"""

    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, related_name="inventory")
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    purchase_price_avg = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Average purchase price"
    )

    class Meta:
        unique_together = ("dealership", "car_model")


class DealershipPreferredSupplier(BaseModel):
    """List of suppliers for each model with the best price"""

    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE)
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    best_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("dealership", "car_model")


class DealershipAction(BaseModel):
    """The car dealership's system of promotions for buyers"""

    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, related_name="customer_actions")
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="The discount percentage is unique for each salon."
    )
    car_models = models.ManyToManyField(CarModel, related_name="actions_in_dealerships")

    def __str__(self):
        return f"{self.dealership.name} - {self.name}"
