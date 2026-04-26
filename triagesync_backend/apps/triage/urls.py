from django.urls import path
from .views import TriageEvaluateView

urlpatterns = [
    path("triage/", TriageEvaluateView.as_view()),
]