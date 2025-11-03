from django.db import models


class BaseModel(models.Model):
    """Abstract base model with common fields: is_active, created_at, updated_at"""

    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
