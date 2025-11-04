from django.db import models

from config.models import BaseModel


class CarSpecification(BaseModel):
    """Car's characteristics"""

    engine_type = models.CharField(max_length=50)
    power_hp = models.IntegerField()
    color = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50)
    body_type = models.CharField(max_length=50)

    db_table = "car_specifications"

    def __str__(self):
        return f"{self.engine_type} / {self.power_hp}hp"


class CarModel(BaseModel):
    """Base car model"""

    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    base_specs = models.ForeignKey(CarSpecification, on_delete=models.PROTECT, related_name="models")

    db_table = "car_models"

    def __str__(self):
        return f"{self.manufacturer} {self.name}"
