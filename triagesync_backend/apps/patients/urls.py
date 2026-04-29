from django.urls import path
from .views import (
    PatientProfileView,
    PatientHistoryView,
    PatientSubmissionDetailView,
    PatientCurrentSessionView,
    TriageSubmissionsHistoryView,
)

urlpatterns = [
    # Patient profile management
    path("profile/", PatientProfileView.as_view(), name="patient-profile"),
    
    # Patient submission history
    path("history/", PatientHistoryView.as_view(), name="patient-history"),
    
    # Current active session
    path("current/", PatientCurrentSessionView.as_view(), name="patient-current-session"),
    
    # Specific submission details
    path("submissions/<int:submission_id>/", PatientSubmissionDetailView.as_view(), name="patient-submission-detail"),
    
    # Triage submissions history (all roles)
    path("triage-submissions/", TriageSubmissionsHistoryView.as_view(), name="triage-submissions-history"),
]
