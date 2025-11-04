from django.contrib import admin

from .models import (
    Dealership,
    DealershipAction,
    DealershipCarInventory,
    DealershipPreferredSupplier,
)


class DealershipCarInventoryInline(admin.TabularInline):
    """Inline for car inventory within the Dealership admin."""

    model = DealershipCarInventory
    extra = 1
    fields = ("car_model", "count", "purchase_price_avg", "is_active")
    readonly_fields = ("purchase_price_avg",)


class DealershipPreferredSupplierInline(admin.TabularInline):
    """Inline for preferred suppliers within the Dealership admin."""

    model = DealershipPreferredSupplier
    extra = 0
    fields = ("car_model", "supplier", "best_price", "last_checked")
    readonly_fields = ("best_price", "last_checked")


class DealershipActionInline(admin.TabularInline):
    """Inline for dealership actions/promotions."""

    model = DealershipAction
    extra = 1
    show_change_link = True
    fields = ("name", "start_date", "end_date", "discount_percentage", "is_active")


@admin.register(Dealership)
class DealershipAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "city", "balance", "admin", "is_active", "created_at")
    list_filter = ("country", "city", "is_active")
    search_fields = ("name", "address", "admin__email")
    readonly_fields = ("balance", "created_at", "updated_at")
    filter_horizontal = ("preferred_specs",)
    fieldsets = (
        (None, {"fields": ("name", "admin", "balance", "is_active")}),
        (
            "Location",
            {"fields": ("country", "city", "address", "location")},
        ),
        (
            "Preferences & Specs",
            {"fields": ("preferred_specs",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    inlines = [
        DealershipCarInventoryInline,
        DealershipPreferredSupplierInline,
    ]

    def location(self, obj):
        return obj.location

    location.short_description = "Location (Formatted)"


@admin.register(DealershipCarInventory)
class DealershipCarInventoryAdmin(admin.ModelAdmin):
    list_display = ("dealership", "car_model", "count", "purchase_price_avg", "is_active")
    list_filter = ("dealership", "car_model__manufacturer", "is_active")
    search_fields = ("dealership__name", "car_model__name")
    readonly_fields = ("purchase_price_avg",)
    list_editable = ("count", "is_active")


@admin.register(DealershipAction)
class DealershipActionAdmin(admin.ModelAdmin):
    list_display = ("name", "dealership", "discount_percentage", "start_date", "end_date", "is_active")
    list_filter = ("dealership", "start_date", "end_date", "is_active")
    search_fields = ("name", "description")
    filter_horizontal = ("car_models",)
