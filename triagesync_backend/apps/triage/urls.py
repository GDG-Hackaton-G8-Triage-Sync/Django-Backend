from django.urls import path
from .views import TriageAIView, TriageEvaluateView

urlpatterns = [
    path('ai/', TriageAIView.as_view(), name='triage-ai'),
    path('evaluate/', TriageEvaluateView.as_view(), name='triage-evaluate'),
]
