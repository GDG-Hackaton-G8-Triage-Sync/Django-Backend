from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes
from triagesync_backend.apps.authentication.permissions import IsStaffOrAdmin
from triagesync_backend.apps.core.pagination import StandardResultsSetPagination
from triagesync_backend.apps.core.response import error_response, validation_error_response, not_found_response
from .serializers import DashboardPatientSerializer, StatusUpdateSerializer, PriorityUpdateSerializer
from rest_framework import serializers
from triagesync_backend.apps.core.serializers import ErrorResponseSerializer, SuccessMessageSerializer
from rest_framework.generics import ListAPIView, GenericAPIView
from .services.dashboard_service import get_patient_queue
from triagesync_backend.apps.patients.models import PatientSubmission
from .services.dashboard_service import update_priority, verify_patient
from django.utils import timezone
from .services.dashboard_service import get_admin_analytics
from .services.dashboard_service import get_admin_overview
from .services.dashboard_service import update_patient_status
from django.core.exceptions import ValidationError


class StaffPatientQueueView(ListAPIView):
    """List patient queue for staff members."""
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    pagination_class = StandardResultsSetPagination
    serializer_class = DashboardPatientSerializer

    def get_queryset(self):
        priority = self.request.query_params.get("priority")
        status_param = self.request.query_params.get("status")
        
        category_param = self.request.query_params.get("category")
        if category_param is not None:
            if category_param == "":
                if "category_filter" in self.request.session:
                    del self.request.session["category_filter"]
                category = None
            else:
                self.request.session["category_filter"] = category_param
                category = category_param
        else:
            category = self.request.session.get("category_filter", None)

        return get_patient_queue(priority, status_param, category)


class UpdatePatientStatusView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    queryset = PatientSubmission.objects.all()
    serializer_class = StatusUpdateSerializer

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
    
class AdminOverviewView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    serializer_class = serializers.Serializer

    def get(self, request):
        data = get_admin_overview()
        return Response(data)
    
class AdminAnalyticsView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    serializer_class = serializers.Serializer

    def get(self, request):
        data = get_admin_analytics()
        return Response(data)
    
class UpdatePatientPriorityView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    queryset = PatientSubmission.objects.all()
    serializer_class = PriorityUpdateSerializer

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
        
class VerifyPatientView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    queryset = PatientSubmission.objects.all()
    serializer_class = serializers.Serializer

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
