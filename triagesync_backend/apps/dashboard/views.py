from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from apps.patients.models import PatientSubmission
from .serializers import DashboardPatientSerializer
from .services.dashboard_service import (
    get_patient_queue,
    update_patient_status,
    get_admin_overview,
    get_admin_analytics,
    update_priority,
    verify_patient
)


# =========================
# STAFF VIEWS
# =========================

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


class UpdatePatientStatusView(APIView):
    """
    PATCH /api/v1/staff/patient/{id}/status/
    """

    def patch(self, request, id):
        status_value = request.data.get("status")

        patient = update_patient_status(id, status_value)

        if not patient:
            return Response(
                {"code": "NOT_FOUND", "message": "Patient not found"},
                status=404
            )

        return Response({"message": "Status updated"})


class UpdatePatientPriorityView(APIView):
    """
    PATCH /api/v1/staff/patient/{id}/priority/
    """

    def patch(self, request, id):
        priority = request.data.get("priority")

        if priority is None:
            return Response(
                {"code": "INVALID_INPUT", "message": "Priority is required"},
                status=400
            )

        try:
            patient = PatientSubmission.objects.get(id=id)
            update_priority(patient, priority)

            return Response({"message": "Priority updated successfully"})

        except PatientSubmission.DoesNotExist:
            return Response(
                {"code": "NOT_FOUND", "message": "Patient not found"},
                status=404
            )


class VerifyPatientView(APIView):
    """
    PATCH /api/v1/staff/patient/{id}/verify/
    """

    def patch(self, request, id):
        try:
            patient = PatientSubmission.objects.get(id=id)

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


# =========================
# ADMIN VIEWS
# =========================

class AdminOverviewView(APIView):
    """
    GET /api/v1/admin/overview/
    """

    def get(self, request):
        data = get_admin_overview()
        return Response(data)


class AdminAnalyticsView(APIView):
    """
    GET /api/v1/admin/analytics/
    """

    def get(self, request):
        data = get_admin_analytics()
        return Response(data)