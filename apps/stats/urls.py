from rest_framework.routers import DefaultRouter

from .views import StatsViewSet

router = DefaultRouter()

router.register(r"stats", StatsViewSet, basename="stats")

urlpatterns = router.urls
