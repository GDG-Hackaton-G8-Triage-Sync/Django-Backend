from django.urls import path
from .views import TriageAIView, TriageEvaluateView, TriagePDFExtractView

urlpatterns = [
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path('pdf-extract/', TriagePDFExtractView.as_view(), name='triage-pdf-extract'),
    path("triage/", TriageEvaluateView.as_view(), name='triage-evaluate'),
]


