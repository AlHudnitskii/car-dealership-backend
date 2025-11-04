from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.dealerships.models import Dealership
from apps.suppliers.models import Supplier
from apps.users.models import CustomerProfile

from .serializers import (
    CustomerStatsSerializer,
    DealershipStatsSerializer,
    GlobalStatsSerializer,
    SupplierStatsSerializer,
)
from .services import CustomerStatsService, DealershipStatsService, GlobalStatsService, SupplierStatsService

User = get_user_model()


class StatsViewSet(viewsets.ViewSet):
    """
    ViewSet for retrieving various system statistics.
    Access to specific stats is controlled by user roles.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="global", permission_classes=[IsAdminUser])
    def global_stats(self, request):
        """Returns overall system statistics (Admins only)."""

        stats_data = GlobalStatsService.get_global_stats()
        serializer = GlobalStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"dealerships/(?P<dealership_pk>\d+)")
    def dealership_stats(self, request, dealership_pk=None):
        """Returns statistics for a specific Dealership."""

        dealership = get_object_or_404(Dealership, pk=dealership_pk)

        if not (request.user.is_staff or request.user.is_superuser or request.user == dealership.admin):
            return Response(
                {"detail": "You do not have permission to view these statistics."}, status=status.HTTP_403_FORBIDDEN
            )

        stats_data = DealershipStatsService.get_dealership_stats(dealership.pk)
        serializer = DealershipStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"customers/(?P<customer_pk>\d+)")
    def customer_stats(self, request, customer_pk=None):
        """Returns statistics for a specific Customer."""

        customer = get_object_or_404(CustomerProfile, pk=customer_pk)

        if not (request.user.is_staff or request.user.is_superuser or request.user == customer.user):
            return Response(
                {"detail": "You do not have permission to view these statistics."}, status=status.HTTP_403_FORBIDDEN
            )

        stats_data = CustomerStatsService.get_customer_stats(customer.pk)
        serializer = CustomerStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me")
    def my_stats(self, request):
        """Returns statistics for the current authenticated user (if Customer)."""

        if not request.user.is_customer or not hasattr(request.user, "customer_profile"):
            return Response(
                {"detail": "User is not a customer or profile not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        customer_profile = request.user.customer_profile
        stats_data = CustomerStatsService.get_customer_stats(customer_profile.pk)
        serializer = CustomerStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"suppliers/(?P<supplier_pk>\d+)")
    def supplier_stats(self, request, supplier_pk=None):
        """Returns statistics for a specific Supplier."""

        supplier = get_object_or_404(Supplier, pk=supplier_pk)

        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "You do not have permission to view these statistics."}, status=status.HTTP_403_FORBIDDEN
            )

        stats_data = SupplierStatsService.get_supplier_stats(supplier.pk)
        serializer = SupplierStatsSerializer(stats_data)
        return Response(serializer.data)
