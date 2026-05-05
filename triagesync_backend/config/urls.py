from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from triagesync_backend.apps.authentication.views import GenericProfileView


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redoc UI
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/v1/auth/", include("triagesync_backend.apps.authentication.urls")),
    path("api/v1/profile/", GenericProfileView.as_view(), name='profile'),  # Direct profile endpoint per API contract
    path("api/v1/patients/", include("triagesync_backend.apps.patients.urls")),
    path("api/v1/dashboard/", include("triagesync_backend.apps.dashboard.urls")),
    path("api/v1/triage/", include("triagesync_backend.apps.triage.urls")),
    path("api/v1/admin/", include("triagesync_backend.apps.api_admin.urls")),
    path("api/v1/notifications/", include("triagesync_backend.apps.notifications.urls")),
    path("", health_check),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
