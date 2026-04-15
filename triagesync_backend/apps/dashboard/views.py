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