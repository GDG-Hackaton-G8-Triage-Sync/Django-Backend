from django.urls import path
from .views import TriageEvaluateView

urlpatterns = [
    path("evaluate/", TriageEvaluateView.as_view()),
]