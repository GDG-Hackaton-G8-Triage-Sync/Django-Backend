from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.patients.models import PatientSubmission
from apps.authentication.permissions import IsMedicalStaff
from apps.core.response import success_response
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

class StaffQueueView(APIView):
    def get(self, request):
        # Mock queue data
        return Response({
            "total": 2,
            "queue": [
                {
                    "session_id": "TS-1111",
                    "priority_level": 1,
                    "urgency_score": 98,
                    "wait_time_seconds": 240
                },
                {
                    "session_id": "TS-2222",
                    "priority_level": 2,
                    "urgency_score": 85,
                    "wait_time_seconds": 600
                }
            ]
        })

class StaffPatientDetailView(APIView):
    def get(self, request, session_id):
        # Mock patient detail data
        return Response({
            "session_id": session_id,
            "symptoms": "Chest pain...",
            "vitals": {
                "hr": 110,
                "spo2": 92
            },
            "ai_reasoning": {
                "condition": "ACS"
            }
        })

class StaffPriorityOverrideView(APIView):
    def post(self, request, session_id):
        # Mock override response
        return Response({"success": True})

class DashboardPatientListView(ListAPIView):
    serializer_class = DashboardPatientSerializer
    permission_classes = [IsAuthenticated, IsMedicalStaff]

    def get_queryset(self):
        queryset = PatientSubmission.objects.select_related("patient").order_by("-created_at")

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return success_response(serializer.data)
