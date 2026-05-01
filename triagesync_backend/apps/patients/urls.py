from django.urls import path
from .views import (
    PatientProfileView,
    PatientHistoryView,
    PatientSubmissionDetailView,
    PatientCurrentSessionView,
    TriageSubmissionsHistoryView,
)
from .clinical_views import (
    ClinicalVerificationView,
    StaffNoteView,
    StaffAssignmentView,
    VitalsHistoryView,
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
    
    # Clinical Workflow (Staff only)
    path("triage/<int:submission_id>/verify/", ClinicalVerificationView.as_view(), name="clinical-verify"),
    path("triage/<int:submission_id>/notes/", StaffNoteView.as_view(), name="staff-notes"),
    path("triage/<int:submission_id>/assign/", StaffAssignmentView.as_view(), name="staff-assign"),
    path("triage/<int:submission_id>/vitals/", VitalsHistoryView.as_view(), name="vitals-log"),
    path("triage/<int:submission_id>/vitals/history/", VitalsHistoryView.as_view(), name="vitals-history"),
]

