from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, CustomerProfileViewSet, UserViewSet

router = DefaultRouter()

router.register(r"users", UserViewSet, basename="user")
router.register(r"customers", CustomerProfileViewSet, basename="customer")
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = router.urls
