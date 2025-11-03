from django.db import models
from vehicles.models import CarModel

from config.models import BaseModel


class Supplier(BaseModel):
    """Supplier model"""

    name = models.CharField(max_length=255, unique=True)
    year_founded = models.IntegerField()
    info = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SupplierCarOffer(BaseModel):
    """Offer on specific car model from supplier"""

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="car_offers")
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("supplier", "car_model")


class SupplierAction(BaseModel):
    """Supplier actions"""

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="actions")
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.supplier.name} - {self.name}"
