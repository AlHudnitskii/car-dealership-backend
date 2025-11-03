from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """Checks if user is a customer."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_customer


class CanCreateOffer(IsCustomer):
    """Allows creating Offer only to customer with confirmed email."""

    def has_permission(self, request, view):
        if view.action == "create":
            return super().has_permission(request, view) and request.user.email_confirmed
        return super().has_permission(request, view)
