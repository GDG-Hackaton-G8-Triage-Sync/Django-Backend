from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes
import csv
from django.http import HttpResponse
from django.db import transaction

from triagesync_backend.apps.authentication.models import User
from triagesync_backend.apps.authentication.permissions import IsAdmin
from triagesync_backend.apps.patients.models import PatientSubmission
from .models import AuditLog, SystemConfig
from triagesync_backend.apps.core.response import error_response
from .serializers import AdminUserSerializer, RoleUpdateSerializer, AuditLogSerializer, SystemConfigSerializer, SuspendUserSerializer
from triagesync_backend.apps.core.serializers import ErrorResponseSerializer, SuccessMessageSerializer
from rest_framework.generics import ListAPIView, UpdateAPIView, DestroyAPIView, GenericAPIView
from .utils import log_action


class AdminUserListView(ListAPIView):
    """List all users in the system (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by('-date_joined')


class AdminUserRoleUpdateView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RoleUpdateSerializer
    queryset = User.objects.all()
    lookup_field = 'user_id'

    def patch(self, request, user_id):
        """Update a user's role (admin only)."""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Invalid input data",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(id=user_id)
                user.role = serializer.validated_data['role']
                user.save()
                
                log_action(
                    actor=request.user,
                    action_type="ROLE_UPDATE",
                    target_description=f"User {user.email} role changed to {user.role}",
                    justification=request.data.get('justification', 'No justification provided')
                )
                
                return Response(
                    {"message": "Role updated successfully"},
                    status=status.HTTP_200_OK
                )
        except User.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminSubmissionDeleteView(DestroyAPIView):
    """Delete a triage submission (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = PatientSubmission.objects.all()
    lookup_url_kwarg = 'submission_id'
    serializer_class = serializers.Serializer

class AdminUserDeleteView(DestroyAPIView):
    """Delete a user (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'
    serializer_class = serializers.Serializer

    def perform_destroy(self, instance):
        user_email = instance.email
        log_action(
            actor=self.request.user,
            action_type="USER_DELETED",
            target_description=f"User {user_email} account erased",
            justification=self.request.data.get('justification', 'No justification provided')
        )
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except User.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AuditLogListView(ListAPIView):
    """List all audit logs in the system (admin only)."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all().order_by('-timestamp')

class AdminUserSuspendView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'user_id'
    serializer_class = SuspendUserSerializer

    def patch(self, request, user_id):
        """Toggle user suspension status (admin only)."""
        is_suspended = request.data.get('is_suspended')
        reason = request.data.get('reason', '')
        
        if is_suspended is None:
            return error_response(
                code="VALIDATION_ERROR",
                message="Field 'is_suspended' is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                user = self.get_object()
                user.is_suspended = is_suspended
                user.suspension_reason = reason
                user.save()
                
                action = "USER_SUSPENDED" if is_suspended else "USER_UNSUSPENDED"
                log_action(
                    actor=request.user,
                    action_type=action,
                    target_description=f"User {user.email} suspension set to {is_suspended}",
                    justification=reason
                )
                
                return Response(
                    {"message": f"User suspension status updated to {is_suspended}"},
                    status=status.HTTP_200_OK
                )
        except User.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemConfigView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer

    def get(self, request):
        """List all system configurations."""
        configs = self.get_queryset()
        data = {c.key: c.value for c in configs}
        return Response(data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update a specific configuration setting."""
        key = request.data.get('key')
        value = request.data.get('value')
        
        if not key:
            return error_response(
                code="VALIDATION_ERROR",
                message="Field 'key' is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            with transaction.atomic():
                config, created = SystemConfig.objects.select_for_update().get_or_create(
                    key=key,
                    defaults={'value': value, 'updated_by': request.user}
                )
                
                if not created:
                    old_value = config.value
                    config.value = value
                    config.updated_by = request.user
                    config.save()
                else:
                    old_value = None
                
                log_action(
                    actor=request.user,
                    action_type="CONFIG_UPDATE",
                    target_description=f"System config '{key}' {'created' if created else 'updated'}",
                    metadata={"old_value": old_value, "new_value": value}
                )
                
                return Response(
                    {"message": f"Config '{key}' {'created' if created else 'updated'} successfully"},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminReportExportView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = PatientSubmission.objects.all()
    serializer_class = serializers.Serializer

    def get(self, request):
        """Export system metrics as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="triagesync_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Patient', 'Condition', 'Priority', 'Status', 'Wait Time (mins)', 'Created At'])
        
        submissions = self.get_queryset().order_by('-created_at')
        
        for sub in submissions:
            wait_time = "N/A"
            if sub.created_at:
                from django.utils import timezone
                delta = timezone.now() - sub.created_at
                wait_time = int(delta.total_seconds() / 60)
                
            writer.writerow([
                sub.id,
                sub.patient.user.username if sub.patient else "Guest",
                sub.condition,
                sub.priority,
                sub.status,
                wait_time,
                sub.created_at.strftime('%Y-%m-%d %H:%M') if sub.created_at else "N/A"
            ])
            
        log_action(
            actor=request.user,
            action_type="REPORT_EXPORT",
            target_description="Generated system-wide triage CSV report"
        )
            
        return response
