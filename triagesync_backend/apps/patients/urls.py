from django.urls import path

from .views import PatientSubmissionView

urlpatterns = [
    path("submit/", PatientSubmissionView.as_view(), name="patient-submit"),
]
