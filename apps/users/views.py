from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import CustomerProfile
from .permissions import IsCustomerOwner
from .serializers import CustomerProfileSerializer, UserRegistrationSerializer, UserSerializer

User = get_user_model()


class UserViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API for viewing User list and details.
    Access: Staff/Superuser for list/retrieve, or retrieve own profile.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list"]:
            permission_classes = [IsAdminUser]
        elif self.action in ["retrieve", "me"]:
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

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all()
        if self.action == "retrieve":
            return User.objects.filter(pk=user.pk)
        return User.objects.none()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """View the authenticated user's profile."""

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CustomerProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    """
    API for managing Customer Profiles.
    Access: Staff/Superuser for list/full CRUD. Retrieve own profile for Customer.
    """

    queryset = CustomerProfile.objects.all().select_related("user")
    serializer_class = CustomerProfileSerializer

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        elif self.action == "retrieve":
            permission_classes = [IsAuthenticated, IsCustomerOwner]
        else:
            permission_classes = [IsAdminUser]

        final_permissions = []
        for perm in permission_classes:
            if isinstance(perm, permissions.BasePermission):
                final_permissions.append(perm)
            else:
                final_permissions.append(perm())

        return final_permissions

    @action(detail=False, methods=["post"], url_path="register", permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Public endpoint for customer registration."""

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Здесь должна быть отправка письма для подтверждения email

        return Response(
            {"detail": "Registration successful. Please check your email to confirm your account."},
            status=status.HTTP_201_CREATED,
        )
