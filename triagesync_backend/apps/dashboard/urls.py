from django.urls import path


from .views import (
    DashboardPatientListView,
    StaffPatientStatusUpdateView,
    AdminOverviewView,
    AdminAnalyticsView,
)

urlpatterns = [
    path("patients/", DashboardPatientListView.as_view(), name="dashboard-patients"),
    path("staff/patient/<int:id>/status/", StaffPatientStatusUpdateView.as_view(), name="staff-patient-status-update"),
    path("admin/overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]
