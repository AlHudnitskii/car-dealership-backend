from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Offer
from .permissions import CanCreateOffer, IsCustomer
from .serializers import OfferCreateSerializer, OfferListSerializer


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
            return [IsAuthenticated(), CanCreateOffer()]
        elif self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), (IsAdminUser | IsCustomer)()]
        return [IsAdminUser()]
