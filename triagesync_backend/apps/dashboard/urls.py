from django.urls import path


from .views import (
    DashboardPatientListView,
    StaffPatientStatusUpdateView,
    AdminOverviewView,
    AdminAnalyticsView,
    StaffQueueView,
    StaffPatientDetailView,
    StaffPriorityOverrideView,
)

urlpatterns = [
    path("patients/", DashboardPatientListView.as_view(), name="dashboard-patients"),
    path("staff/queue/", StaffQueueView.as_view(), name="staff-queue"),
    path("staff/patient/<str:session_id>/", StaffPatientDetailView.as_view(), name="staff-patient-detail"),
    path("staff/patient/<str:session_id>/override/", StaffPriorityOverrideView.as_view(), name="staff-priority-override"),
    path("staff/patient/<int:id>/status/", StaffPatientStatusUpdateView.as_view(), name="staff-patient-status-update"),
    path("admin/overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]
