from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.dealerships.urls import router as dealership_router
from apps.stats.urls import router as stats_router
from apps.suppliers.urls import router as supplier_router
from apps.transactions.urls import router as transaction_router
from apps.users.urls import router as user_router
from apps.vehicles.urls import router as vehicle_router

router = DefaultRouter()

router.registry.extend(stats_router.registry)
router.registry.extend(supplier_router.registry)
router.registry.extend(dealership_router.registry)
router.registry.extend(transaction_router.registry)
router.registry.extend(vehicle_router.registry)
router.registry.extend(user_router.registry)

schema_view = get_schema_view(
    openapi.Info(
        title="Car Dealership API",
        default_version="v1",
        description="API documentation for the Car Dealership Management System",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[
        permissions.AllowAny,
    ],
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/docs/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/docs/swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
