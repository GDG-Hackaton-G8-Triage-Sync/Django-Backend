from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from triagesync_backend.apps.authentication.permissions import IsStaffOrAdmin
from triagesync_backend.apps.core.pagination import StandardResultsSetPagination
from triagesync_backend.apps.core.response import error_response, validation_error_response, not_found_response
from .serializers import DashboardPatientSerializer
from .services.dashboard_service import get_patient_queue
from triagesync_backend.apps.patients.models import PatientSubmission
from .services.dashboard_service import update_priority, verify_patient
from django.utils import timezone
from .services.dashboard_service import get_admin_analytics
from .services.dashboard_service import get_admin_overview
from .services.dashboard_service import update_patient_status
from django.core.exceptions import ValidationError


class StaffPatientQueueView(APIView):
    """
    GET /api/v1/staff/patients/
    Staff patient queue with pagination
    Query params: priority, status, page, page_size (default 20, max 100)
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        priority = request.query_params.get("priority")
        status_param = request.query_params.get("status")

        patients = get_patient_queue(priority, status_param)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_patients = paginator.paginate_queryset(patients, request)
        
        serializer = DashboardPatientSerializer(paginated_patients, many=True)

        return paginator.get_paginated_response(serializer.data)


class UpdatePatientStatusView(APIView):
    """
    PATCH /api/v1/staff/patient/{id}/status/
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, id):
        new_status = request.data.get("status")

        if not new_status:
            return validation_error_response("Status is required")

        try:
            patient = update_patient_status(id, new_status)

            if not patient:
                return not_found_response("Patient not found")

            return Response({"message": "Status updated successfully"})
            
        except (ValueError, ValidationError) as e:
            return error_response(
                code="INVALID_TRANSITION",
                message=str(e),
                status_code=400
            )
    
class AdminOverviewView(APIView):
    """
    GET /api/v1/admin/overview/
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get(self, request):
        data = get_admin_overview()
        return Response(data)
    
class AdminAnalyticsView(APIView):
    """
    GET /api/v1/admin/analytics/
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get(self, request):
        data = get_admin_analytics()
        return Response(data)
    
class UpdatePatientPriorityView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, id):
        priority = request.data.get("priority")

        if priority is None:
            return error_response(
                code="INVALID_INPUT",
                message="Priority is required",
                status_code=400
            )

        # Convert to integer if it's a string
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            return error_response(
                code="INVALID_INPUT",
                message="Priority must be a valid integer",
                status_code=400
            )

        try:
            patient = PatientSubmission.objects.get(id=id)

            # 👉 call service instead of writing logic here
            update_priority(patient, priority)

            return Response({"message": "Priority updated successfully"})

        except PatientSubmission.DoesNotExist:
            return not_found_response("Patient not found")
        except ValueError as e:
            return error_response(
                code="INVALID_INPUT",
                message=str(e),
                status_code=400
            )
        
class VerifyPatientView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, id):
        try:
            patient = PatientSubmission.objects.get(id=id)

            # 👉 call service
            result = verify_patient(patient, request.user)

            if result is None:
                return error_response(
                    code="ALREADY_VERIFIED",
                    message="Patient already verified",
                    status_code=400
                )

            return Response({"message": "Patient verified successfully"})

        except PatientSubmission.DoesNotExist:
            return not_found_response("Patient not found")
