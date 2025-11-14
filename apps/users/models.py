from django.contrib.auth.models import AbstractUser
from django.db import models

from config.models import BaseModel

from .managers import UserManager


class User(AbstractUser):
    """Custom User Profile with addiction roles"""

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)

    is_customer = models.BooleanField(default=False)
    is_dealership_admin = models.BooleanField(default=False)
    is_supplier_admin = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False, verbose_name="Email confirmed")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    db_table = "users"

    def __str__(self):
        return self.email


class CustomerProfile(BaseModel):
    """Customer Profile"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    auto_generated_info = models.JSONField(default=dict, blank=True, null=True)

    db_table = "customer_profiles"

    def __str__(self):
        return f"Profile of {self.user.email}"
