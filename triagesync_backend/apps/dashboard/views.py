
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView

from triagesync_backend.apps.patients.models import PatientSubmission

from .serializers import DashboardPatientSerializer
from .services.dashboard_service import get_patient_queue
from apps.patients.models import PatientSubmission
from .services.dashboard_service import update_priority, verify_patient

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

class StaffPatientQueueView(APIView):
    """
    GET /api/v1/staff/patients/
    """

    def get(self, request):
        priority = request.query_params.get("priority")
        status = request.query_params.get("status")

        patients = get_patient_queue(priority, status)
        serializer = DashboardPatientSerializer(patients, many=True)

        return Response(serializer.data)

from .services.dashboard_service import update_patient_status


class UpdatePatientStatusView(APIView):
    """
    PATCH /api/v1/staff/patient/{id}/status/
    """

    def patch(self, request, id):
        status = request.data.get("status")

        patient = update_patient_status(id, status)

        if not patient:
            return Response({"error": "Patient not found"}, status=404)

        return Response({"message": "Status updated"})
    
from .services.dashboard_service import get_admin_overview


class AdminOverviewView(APIView):
    """
    GET /api/v1/admin/overview/
    """

    def get(self, request):
        data = get_admin_overview()
        return Response(data)
    
from .services.dashboard_service import get_admin_analytics


class AdminAnalyticsView(APIView):
    """
    GET /api/v1/admin/analytics/
    """

    def get(self, request):
        data = get_admin_analytics()
        return Response(data)
    
class UpdatePatientPriorityView(APIView):

    def patch(self, request, id):
        priority = request.data.get("priority")

        if priority is None:
            return Response(
                {"code": "INVALID_INPUT", "message": "Priority is required"},
                status=400
            )

        try:
            patient = PatientSubmission.objects.get(id=id)

            # 👉 call service instead of writing logic here
            update_priority(patient, priority)

            return Response({"message": "Priority updated successfully"})

        except PatientSubmission.DoesNotExist:
            return Response(
                {"code": "NOT_FOUND", "message": "Patient not found"},
                status=404
            )
        

from django.utils import timezone


class VerifyPatientView(APIView):

    def patch(self, request, id):
        try:
            patient = PatientSubmission.objects.get(id=id)

            # 👉 call service
            result = verify_patient(patient, request.user)

            if result is None:
                return Response(
                    {
                        "code": "ALREADY_VERIFIED",
                        "message": "Patient already verified"
                    },
                    status=400
                )

            return Response({"message": "Patient verified successfully"})

        except PatientSubmission.DoesNotExist:
            return Response(
                {"code": "NOT_FOUND", "message": "Patient not found"},
                status=404
            )