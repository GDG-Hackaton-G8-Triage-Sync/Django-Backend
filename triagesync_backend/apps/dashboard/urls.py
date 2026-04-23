from django.urls import path

from .views import DashboardPatientListView

urlpatterns = [
    path("patients/", DashboardPatientListView.as_view(), name="dashboard-patients"),
]
