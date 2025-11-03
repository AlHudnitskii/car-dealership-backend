from dealerships.models import Dealership
from django.contrib.contenttypes.fields import ContentType, GenericForeignKey
from django.db import models
from users.models import CustomerProfile
from vehicles.models import CarModel

from config.models import BaseModel


class Offer(BaseModel):
    """Purchase offer from a customer"""

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("MATCHED", "Matched"),
        ("REJECTED", "Rejected"),
        ("BOUGHT", "Bought"),
    )

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="offers")
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    dealership_match = models.ForeignKey(Dealership, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Offer {self.id} by {self.customer.user.email} - Status: {self.status}"


class Transaction(BaseModel):
    """Universal model for all transactions (Purchase, Sale)"""

    TYPE_CHOICES = (
        ("SALE", "Sale to customer"),
        ("PURCHASE", "Purchase from supplier"),
    )

    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    car_model = models.ForeignKey(CarModel, on_delete=models.PROTECT)
    count = models.PositiveIntegerField(default=1)

    sender_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name="sender_transactions")
    sender_object_id = models.PositiveIntegerField()
    sender = GenericForeignKey("sender_content_type", "sender_object_id")

    recipient_content_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, related_name="recipient_transactions"
    )
    recipient_object_id = models.PositiveIntegerField()
    recipient = GenericForeignKey("recipient_content_type", "recipient_object_id")

    def __str__(self):
        return f"{self.transaction_type} {self.id} - {self.amount} USD"
