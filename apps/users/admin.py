from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomerProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "is_customer",
        "is_dealership_admin",
        "is_supplier_admin",
        "email_confirmed",
        "is_staff",
    )
    list_filter = ("is_customer", "is_dealership_admin", "is_supplier_admin", "email_confirmed", "is_staff")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        (
            "Roles",
            {
                "fields": (
                    "is_customer",
                    "is_dealership_admin",
                    "is_supplier_admin",
                )
            },
        ),
        ("Status", {"fields": ("email_confirmed", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "is_customer",
                    "is_dealership_admin",
                    "is_supplier_admin",
                ),
            },
        ),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)
