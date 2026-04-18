from django.contrib import admin

from django.http import JsonResponse
from django.urls import include, path

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("triagesync_backend.apps.authentication.urls")),
    path("api/v1/patients/", include("triagesync_backend.apps.patients.urls")),
    path("api/v1/dashboard/", include("triagesync_backend.apps.dashboard.urls")),
    path("api/v1/triage/", include("triagesync_backend.apps.triage.urls")),
    path("", health_check),
]

