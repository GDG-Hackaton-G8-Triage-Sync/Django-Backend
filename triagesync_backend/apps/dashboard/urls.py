from django.urls import path
from .views import (
    StaffPatientQueueView,
    UpdatePatientStatusView,
    AdminOverviewView,
    AdminAnalyticsView,
    UpdatePatientPriorityView,
    VerifyPatientView,
)

urlpatterns = [
    # STAFF
    path("staff/patients/", StaffPatientQueueView.as_view()),
    path("staff/patient/<int:id>/status/", UpdatePatientStatusView.as_view()),
    path("staff/patient/<int:id>/priority/", UpdatePatientPriorityView.as_view()),
    path("staff/patient/<int:id>/verify/", VerifyPatientView.as_view()),

    # ADMIN
    path("admin/overview/", AdminOverviewView.as_view()),
    path("admin/analytics/", AdminAnalyticsView.as_view()),
]