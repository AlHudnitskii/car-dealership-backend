from rest_framework.routers import DefaultRouter

from .views import SupplierActionViewSet, SupplierCarOfferViewSet, SupplierViewSet

router = DefaultRouter()

router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"supplier-offers", SupplierCarOfferViewSet, basename="supplieroffer")
router.register(r"supplier-actions", SupplierActionViewSet, basename="supplieraction")

urlpatterns = router.urls
