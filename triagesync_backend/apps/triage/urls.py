from django.urls import path
from .views import (
    TriageAIView,
    TriageEvaluateView,
    TriagePDFExtractView,
    TriageSubmissionView,
    TriageWaitingAnalyticsView,
)

urlpatterns = [
    # Main triage submission endpoint (API contract)
    path("", TriageSubmissionView.as_view(), name='triage-submit'),
    
    # Additional AI endpoints
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path('pdf-extract/', TriagePDFExtractView.as_view(), name='triage-pdf-extract'),
    path("evaluate/", TriageEvaluateView.as_view(), name='triage-evaluate'),
    path("<int:id>/waiting-analytics/", TriageWaitingAnalyticsView.as_view(), name="triage-waiting-analytics"),
]


