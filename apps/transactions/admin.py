from django.contrib import admin

from .models import Offer, Transaction


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "car_model", "max_price", "status", "dealership_match", "is_active", "created_at")
    list_filter = ("status", "is_active", "dealership_match")
    search_fields = ("customer__user__email", "car_model__name", "dealership_match__name")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "transaction_type",
        "amount",
        "car_model",
        "count",
        "sender_object",
        "recipient_object",
        "created_at",
    )
    list_filter = ("transaction_type", "car_model__manufacturer", "created_at")
    search_fields = ("car_model__name",)
    readonly_fields = (
        "transaction_type",
        "amount",
        "car_model",
        "count",
        "sender_content_type",
        "sender_object_id",
        "recipient_content_type",
        "recipient_object_id",
        "created_at",
        "updated_at",
    )

    def sender_object(self, obj):
        return obj.sender

    def recipient_object(self, obj):
        return obj.recipient

    sender_object.short_description = "Sender"
    recipient_object.short_description = "Recipient"
