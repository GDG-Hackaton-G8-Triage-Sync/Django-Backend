"""
Staff-facing URL routes for clinical workflow actions.

These routes are mounted at /api/v1/staff/ and mirror the triage-based
clinical views so the Flutter frontend can call the expected paths:

  GET/POST  /api/v1/staff/patient/{id}/notes/
  PATCH     /api/v1/staff/patient/{id}/assign/
  GET/POST  /api/v1/staff/patient/{id}/vitals/history/
  PATCH     /api/v1/staff/patient/{id}/verify/
"""

from django.urls import path
from triagesync_backend.apps.patients.clinical_views import (
    ClinicalVerificationView,
    StaffNoteView,
    StaffAssignmentView,
    VitalsHistoryView,
)

urlpatterns = [
    path("patient/<int:submission_id>/notes/", StaffNoteView.as_view(), name="staff-notes-v2"),
    path("patient/<int:submission_id>/assign/", StaffAssignmentView.as_view(), name="staff-assign-v2"),
    path("patient/<int:submission_id>/vitals/history/", VitalsHistoryView.as_view(), name="staff-vitals-history-v2"),
    path("patient/<int:submission_id>/verify/", ClinicalVerificationView.as_view(), name="staff-verify-v2"),
]
