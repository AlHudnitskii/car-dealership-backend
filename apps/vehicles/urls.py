from rest_framework.routers import DefaultRouter

from .views import CarModelViewSet, CarSpecificationViewSet

router = DefaultRouter()

router.register(r"car-specifications", CarSpecificationViewSet, basename="carspecification")
router.register(r"car-models", CarModelViewSet, basename="carmodel")

urlpatterns = router.urls
