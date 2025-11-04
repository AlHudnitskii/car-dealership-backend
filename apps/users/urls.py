from rest_framework.routers import DefaultRouter

from .views import CustomerProfileViewSet, UserViewSet

router = DefaultRouter()

router.register(r"users", UserViewSet, basename="user")
router.register(r"customers", CustomerProfileViewSet, basename="customer")

urlpatterns = router.urls
