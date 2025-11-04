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


class IsStaffOrOwner(permissions.BasePermission):
    """Allows access to Staff/Superuser or the transaction sender/recipient."""

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_staff or user.is_superuser:
            return True

        is_sender = False
        is_recipient = False

        if user.is_customer and hasattr(user, "customer_profile"):
            if obj.sender == user.customer_profile or obj.recipient == user.customer_profile:
                is_sender = is_recipient = True

        # TODO: Добавить проверку для Dealership/Supplier admins, если они являются сторонами транзакции.

        if request.method in permissions.SAFE_METHODS:
            return is_sender or is_recipient
        return False


class OrPermission(permissions.BasePermission):
    """
    A permission that passes if ANY of the given permissions are granted (OR logic).
    Used to group two permissions: OrPermission(Perm1, Perm2).
    """

    def __init__(self, *permissions):
        self.permissions = permissions

    def has_permission(self, request, view):
        for PermissionClass in self.permissions:
            if PermissionClass().has_permission(request, view):
                return True
        return False

    def has_object_permission(self, request, view, obj):
        for PermissionClass in self.permissions:
            if hasattr(PermissionClass, "has_object_permission"):
                if PermissionClass().has_object_permission(request, view, obj):
                    return True
        return False
