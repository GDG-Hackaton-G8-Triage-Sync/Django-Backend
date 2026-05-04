from django.urls import path
from .views import (
    PatientProfileView,
    PatientHistoryView,
    PatientSubmissionDetailView,
    PatientCurrentSessionView,
    PatientQueueView,
    TriageSubmissionsHistoryView,
    ProfilePhotoUploadView,
    ProfilePhotoDeleteView,
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
    
    # Profile photo management
    path("profile/photo/", ProfilePhotoUploadView.as_view(), name="profile-photo-upload"),
    path("profile/photo/", ProfilePhotoDeleteView.as_view(), name="profile-photo-delete"),
    
    # Patient submission history
    path("history/", PatientHistoryView.as_view(), name="patient-history"),
    
    # Current active session
    path("current/", PatientCurrentSessionView.as_view(), name="patient-current-session"),

    # Patient queue tracker
    path("queue/", PatientQueueView.as_view(), name="patient-queue"),
    
    # Specific submission details
    path("submissions/<int:submission_id>/", PatientSubmissionDetailView.as_view(), name="patient-submission-detail"),
    
    # Triage submissions history (all roles)
    path("triage-submissions/", TriageSubmissionsHistoryView.as_view(), name="triage-submissions-history"),
]
