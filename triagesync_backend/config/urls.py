from django.contrib import admin

from django.http import JsonResponse
from django.urls import include, path

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/patients/", include("apps.patients.urls")),
    path("api/v1/", include("apps.dashboard.urls")),
    ]
