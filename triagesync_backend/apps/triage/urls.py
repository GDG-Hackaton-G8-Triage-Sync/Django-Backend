from django.urls import path
from .views import TriageAIView, TriageEvaluateView, TriagePDFExtractView, TriageSubmissionView

urlpatterns = [
    # Main triage submission endpoint (API contract)
    path("", TriageSubmissionView.as_view(), name='triage-submit'),
    
    # Additional AI endpoints
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path('pdf-extract/', TriagePDFExtractView.as_view(), name='triage-pdf-extract'),
    path("evaluate/", TriageEvaluateView.as_view(), name='triage-evaluate'),
]


