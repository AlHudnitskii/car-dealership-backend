from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.transactions.views import OfferViewSet

router = DefaultRouter()
router.register(r"offers", OfferViewSet, basename="offer")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
    path("api/", include(router.urls)),
    path("api/docs/", include("drf_yasg.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]
