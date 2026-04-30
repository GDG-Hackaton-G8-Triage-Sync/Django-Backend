from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from triagesync_backend.apps.authentication.views import GenericProfileView
from triagesync_backend.apps.patients.views import TriageSubmissionsHistoryView


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("triagesync_backend.apps.authentication.urls")),
    path("api/v1/profile/", GenericProfileView.as_view(), name="profile"),
    path("api/v1/patients/", include("triagesync_backend.apps.patients.urls")),
    path("api/v1/triage-submissions/", TriageSubmissionsHistoryView.as_view(), name="triage-submissions-top-level"),
    path("api/v1/dashboard/", include("triagesync_backend.apps.dashboard.urls")),
    path("api/v1/triage/", include("triagesync_backend.apps.triage.urls")),
    path("api/v1/admin/", include("triagesync_backend.apps.api_admin.urls")),
    path("api/v1/notifications/", include("triagesync_backend.apps.notifications.urls")),
    path("", health_check),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
