from rest_framework import permissions


class IsSupplierAdmin(permissions.BasePermission):
    """Checks if user is a supplier admin."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_supplier_admin


class IsOwnerOfSupplier(permissions.BasePermission):
    """Allows access only to the supplier admin."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_supplier_admin


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
