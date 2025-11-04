from django.contrib import admin

from .models import CarModel, CarSpecification


class CarModelInline(admin.TabularInline):
    """Inline for models using this specification."""

    model = CarModel
    extra = 0
    fields = ("name", "manufacturer", "is_active")
    readonly_fields = ("name", "manufacturer", "is_active")
    show_change_link = True


@admin.register(CarSpecification)
class CarSpecificationAdmin(admin.ModelAdmin):
    list_display = ("id", "engine_type", "power_hp", "transmission", "body_type", "is_active")
    list_filter = ("engine_type", "transmission", "body_type", "is_active")
    search_fields = ("engine_type", "color")
    list_editable = ("is_active",)

    inlines = [CarModelInline]


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ("manufacturer", "name", "base_specs", "is_active", "created_at")
    list_filter = ("manufacturer", "is_active")
    search_fields = ("manufacturer", "name")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
