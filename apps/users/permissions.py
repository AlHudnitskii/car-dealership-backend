from rest_framework import permissions


class IsCustomerOwner(permissions.BasePermission):
    """
    Allows access only to the profile owner or Staff/Superuser.
    Used for CustomerProfile detail view.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff or request.user.is_superuser:
                return True
            return obj.user == request.user
        return request.user.is_staff or request.user.is_superuser
