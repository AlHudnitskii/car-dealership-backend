from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Offer, Transaction
from .permissions import CanCreateOffer, IsCustomer, IsStaffOrOwner, OrPermission
from .serializers import OfferCreateSerializer, OfferListSerializer, TransactionSerializer


class OfferViewSet(viewsets.ModelViewSet):
    """
    API for managing Offers.
    Customers: only creation (with confirmed email) and viewing their own.
    Admins/Staff: full access.
    """

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Offer.objects.all().order_by("-created_at")
        elif user.is_customer:
            return Offer.objects.filter(customer__user=user).order_by("-created_at")
        return Offer.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return OfferCreateSerializer
        return OfferListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated, CanCreateOffer()]
        elif self.action in ["list", "retrieve"]:
            return [IsAuthenticated, (OrPermission(IsAdminUser, IsCustomer()))]
        return [IsAdminUser()]


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API for managing Transactions.
    ReadOnly: Transactions should not be modifiable via API.
    Access: Staff/Superusers or the transaction parties.
    """

    serializer_class = TransactionSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["transaction_type", "car_model"]
    ordering_fields = ["amount", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Transaction.objects.all().order_by("-created_at")

        if user.is_customer and hasattr(user, "customer_profile"):
            customer_profile = user.customer_profile
            customer_ct = ContentType.objects.get_for_model(customer_profile)

            return Transaction.objects.filter(
                models.Q(sender_content_type=customer_ct, sender_object_id=customer_profile.pk)
                | models.Q(recipient_content_type=customer_ct, recipient_object_id=customer_profile.pk)
            ).order_by("-created_at")

        return Transaction.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated, OrPermission(IsAdminUser, IsStaffOrOwner)]
        return [permissions.IsAdminUser()]
