from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView

from apps.patients.models import PatientSubmission

from .serializers import DashboardPatientSerializer
class StaffPatientStatusUpdateView(APIView):
    def patch(self, request, id):
        # Mock response for status update
        return Response({"id": id, "status": request.data.get("status", "in_progress")}, status=status.HTTP_200_OK)

class AdminOverviewView(APIView):
    def get(self, request):
        # Mock admin overview data
        return Response({
            "total_patients": 120,
            "waiting": 45,
            "in_progress": 30,
            "completed": 45,
            "critical_cases": 10
        })

class AdminAnalyticsView(APIView):
    def get(self, request):
        # Mock analytics data
        return Response({
            "avg_urgency_score": 67,
            "peak_hour": "14:00",
            "common_conditions": ["Cardiac Event", "Migraine"]
        })
class DashboardPatientListView(ListAPIView):
    queryset = PatientSubmission.objects.select_related("patient").order_by("-created_at")
    serializer_class = DashboardPatientSerializer
