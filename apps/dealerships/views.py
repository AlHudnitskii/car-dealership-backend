from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import (
    Dealership,
    DealershipAction,
    DealershipCarInventory,
    DealershipPreferredSupplier,
)
from .permissions import IsDealershipOwner, IsDealershipStaff, OrPermission
from .serializers import (
    DealershipActionSerializer,
    DealershipCarInventorySerializer,
    DealershipDetailSerializer,
    DealershipListSerializer,
    DealershipPreferredSupplierSerializer,
)


class DealershipViewSet(viewsets.ModelViewSet):
    """API for managing Dealerships. Full access for Admins, restricted for others."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country", "city"]
    search_fields = ["name", "address", "city"]
    ordering_fields = ["name", "balance", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Dealership.objects.all()
        elif user.is_dealership_admin and hasattr(user, "managed_dealership"):
            return Dealership.objects.filter(admin=user)
        return Dealership.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "list":
            return DealershipListSerializer
        return DealershipDetailSerializer

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            permission_classes = [IsAdminUser]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsDealershipOwner)]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class DealershipCarInventoryViewSet(viewsets.ModelViewSet):
    """API for managing car stock in dealerships. Access restricted to Staff/Dealership Admins."""

    serializer_class = DealershipCarInventorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["dealership", "car_model"]
    ordering_fields = ["count", "purchase_price_avg"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return DealershipCarInventory.objects.all()
        elif user.is_dealership_admin and hasattr(user, "managed_dealership"):
            return DealershipCarInventory.objects.filter(dealership__admin=user)
        return DealershipCarInventory.objects.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsDealershipStaff)]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class DealershipPreferredSupplierViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing preferred suppliers. Only read-only, management handled by Celery/Admins."""

    serializer_class = DealershipPreferredSupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["dealership", "car_model", "supplier"]
    ordering_fields = ["best_price", "last_checked"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return DealershipPreferredSupplier.objects.all()
        elif user.is_dealership_admin and hasattr(user, "managed_dealership"):
            return DealershipPreferredSupplier.objects.filter(dealership__admin=user)
        return DealershipPreferredSupplier.objects.none()

    def get_permissions(self):
        permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsDealershipStaff)]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class DealershipActionViewSet(viewsets.ModelViewSet):
    """API for managing dealership promotions/actions. Access restricted to Staff/Dealership Admins."""

    serializer_class = DealershipActionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["dealership", "start_date", "end_date"]
    search_fields = ["name", "description"]
    ordering_fields = ["start_date", "discount_percentage"]

    def get_queryset(self):
        user = self.request.user
        queryset = DealershipAction.objects.all()
        if user.is_staff or user.is_superuser:
            return queryset
        elif user.is_dealership_admin and hasattr(user, "managed_dealership"):
            return queryset.filter(dealership__admin=user)
        return queryset.filter(is_active=True, dealership__is_active=True).distinct()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsDealershipStaff)]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions
