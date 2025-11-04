from rest_framework.routers import DefaultRouter

from .views import (
    DealershipActionViewSet,
    DealershipCarInventoryViewSet,
    DealershipPreferredSupplierViewSet,
    DealershipViewSet,
)

router = DefaultRouter()

router.register(r"dealerships", DealershipViewSet, basename="dealership")
router.register(r"dealership-inventory", DealershipCarInventoryViewSet, basename="dealershipinventory")
router.register(r"dealership-suppliers", DealershipPreferredSupplierViewSet, basename="dealershipsupplier")
router.register(r"dealership-actions", DealershipActionViewSet, basename="dealershipaction")

urlpatterns = router.urls
