from rest_framework import permissions


class IsDealershipOwner(permissions.BasePermission):
    """Allows access only to dealership admin."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.admin == request.user


class IsDealershipStaff(permissions.BasePermission):
    """Checks if user is a dealership admin."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_dealership_admin
