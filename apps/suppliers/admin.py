from django.contrib import admin

from .models import Supplier, SupplierAction, SupplierCarOffer


class SupplierCarOfferInline(admin.TabularInline):
    """Inline for car offers within the Supplier admin."""

    model = SupplierCarOffer
    extra = 1
    fields = ("car_model", "price", "stock_count", "is_active")


class SupplierActionInline(admin.TabularInline):
    """Inline for supplier actions/promotions."""

    model = SupplierAction
    extra = 1
    show_change_link = True
    fields = ("name", "start_date", "end_date", "discount_percentage", "is_active")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "year_founded", "is_active", "created_at")
    list_filter = ("year_founded", "is_active")
    search_fields = ("name", "info")
    readonly_fields = ("created_at", "updated_at")

    inlines = [
        SupplierCarOfferInline,
        SupplierActionInline,
    ]


@admin.register(SupplierCarOffer)
class SupplierCarOfferAdmin(admin.ModelAdmin):
    list_display = ("supplier", "car_model", "price", "stock_count", "is_active")
    list_filter = ("supplier", "car_model__manufacturer", "is_active")
    search_fields = ("supplier__name", "car_model__name")
    list_editable = ("price", "stock_count", "is_active")


@admin.register(SupplierAction)
class SupplierActionAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier", "discount_percentage", "start_date", "end_date", "is_active")
    list_filter = ("supplier", "start_date", "end_date", "is_active")
    search_fields = ("name", "description")
