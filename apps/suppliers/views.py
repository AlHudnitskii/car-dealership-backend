# apps/suppliers/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Supplier, SupplierAction, SupplierCarOffer
from .permissions import IsSupplierAdmin, OrPermission
from .serializers import (
    SupplierActionSerializer,
    SupplierCarOfferListSerializer,
    SupplierCarOfferManageSerializer,
    SupplierSerializer,
)


class SupplierViewSet(viewsets.ModelViewSet):
    """API for managing Suppliers. Full access for Admins, read-only for others."""

    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all().prefetch_related("car_offers")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["year_founded", "is_active"]
    search_fields = ["name", "info"]
    ordering_fields = ["name", "year_founded", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser()]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class SupplierCarOfferViewSet(viewsets.ModelViewSet):
    """API for managing car offers from suppliers. Full access for Admins/Supplier Admins, read-only for others."""

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["supplier", "car_model", "price", "is_active"]
    ordering_fields = ["price", "stock_count", "updated_at"]

    def get_queryset(self):
        queryset = SupplierCarOffer.objects.filter(is_active=True).select_related("supplier", "car_model")

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return SupplierCarOffer.objects.all().select_related("supplier", "car_model")
        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SupplierCarOfferManageSerializer
        return SupplierCarOfferListSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsSupplierAdmin)]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class SupplierActionViewSet(viewsets.ModelViewSet):
    """API for managing supplier promotions/actions. Full access for Admins/Supplier Admins, read-only for others."""

    serializer_class = SupplierActionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["supplier", "start_date", "end_date", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["start_date", "discount_percentage"]

    def get_queryset(self):
        queryset = SupplierAction.objects.filter(is_active=True)

        user = self.request.user
        if user.is_staff or user.is_superuser or user.is_supplier_admin:
            return SupplierAction.objects.all()
        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, OrPermission(IsAdminUser, IsSupplierAdmin)]
        else:
            permission_classes = [IsAuthenticated]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions
