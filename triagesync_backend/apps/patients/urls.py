from django.urls import path


from .views import PatientSubmissionView, PatientTriageView, PatientCurrentSessionView, PatientFileUploadView

urlpatterns = [
    path("submit/", PatientSubmissionView.as_view(), name="patient-submit"),
    path("patient/triage/", PatientTriageView.as_view(), name="patient-triage"),
    path("patient/triage/current/", PatientCurrentSessionView.as_view(), name="patient-triage-current"),
    path("patient/triage/upload/", PatientFileUploadView.as_view(), name="patient-triage-upload"),
]
