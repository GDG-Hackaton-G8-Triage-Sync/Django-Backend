from django.urls import path
from .views import TriageAIView, TriageEvaluateView, TriageSubmissionView
from triagesync_backend.apps.patients.clinical_views import (
    ClinicalVerificationView,
    StaffNoteView,
    StaffAssignmentView,
    VitalsHistoryView,
)

urlpatterns = [
    # Main triage submission endpoint (API contract)
    path("", TriageSubmissionView.as_view(), name='triage-submit'),
    
    # Combined AI triage endpoint
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path("evaluate/", TriageEvaluateView.as_view(), name='triage-evaluate'),
    
    # Clinical Workflow (Staff only)
    path("<int:submission_id>/verify/", ClinicalVerificationView.as_view(), name="clinical-verify"),
    path("<int:submission_id>/notes/", StaffNoteView.as_view(), name="staff-notes"),
    path("<int:submission_id>/assign/", StaffAssignmentView.as_view(), name="staff-assign"),
    path("<int:submission_id>/vitals/", VitalsHistoryView.as_view(), name="vitals-log"),
    path("<int:submission_id>/vitals/history/", VitalsHistoryView.as_view(), name="vitals-history"),
]
