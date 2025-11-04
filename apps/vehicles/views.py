from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import CarModel, CarSpecification
from .serializers import (
    CarModelDetailSerializer,
    CarModelListCreateSerializer,
    CarSpecificationSerializer,
)


class CarSpecificationViewSet(viewsets.ModelViewSet):
    """
    API for managing Car Specifications.
    Access: Read-only for authenticated users, full CRUD for Staff/Superusers.
    """

    serializer_class = CarSpecificationSerializer
    queryset = CarSpecification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["engine_type", "transmission", "body_type"]
    search_fields = ["engine_type", "color", "body_type"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions


class CarModelViewSet(viewsets.ModelViewSet):
    """
    API for managing Car Models.
    Access: Read-only for authenticated users, full CRUD for Staff/Superusers.
    """

    queryset = CarModel.objects.all().select_related("base_specs")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["manufacturer", "is_active", "base_specs__engine_type"]
    search_fields = ["name", "manufacturer"]
    ordering_fields = ["manufacturer", "name", "base_specs__power_hp"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CarModelDetailSerializer
        return CarModelListCreateSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions
