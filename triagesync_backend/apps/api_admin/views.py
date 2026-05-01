from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import csv
from django.http import HttpResponse
from django.db import transaction

from triagesync_backend.apps.authentication.models import User
from triagesync_backend.apps.authentication.permissions import IsAdmin
from triagesync_backend.apps.patients.models import PatientSubmission
from .models import AuditLog
from triagesync_backend.apps.core.response import error_response
from .serializers import AdminUserSerializer, RoleUpdateSerializer, AuditLogSerializer
from .utils import log_action


class AdminUserListView(APIView):
    """
    Admin user listing endpoint.
    
    GET /api/v1/admin/users/
    Returns all users ordered by date_joined descending (admin only).
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """List all users in the system (admin only)."""
        users = User.objects.all().order_by('-date_joined')
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserRoleUpdateView(APIView):
    """
    Admin role management endpoint.
    
    PATCH /api/v1/admin/users/{id}/role/
    Updates a user's role (admin only).
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 9.2, 9.4
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def patch(self, request, user_id):
        """Update a user's role (admin only)."""
        serializer = RoleUpdateSerializer(data=request.data)
        
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


class AdminSubmissionDeleteView(APIView):
    """
    Admin submission deletion endpoint.
    
    DELETE /api/v1/admin/patient/{id}/
    Deletes a triage submission (admin only).
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 9.3, 9.4
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def delete(self, request, submission_id):
        """Delete a triage submission (admin only)."""
        try:
            with transaction.atomic():
                submission = PatientSubmission.objects.select_for_update().get(id=submission_id)
                submission.delete()
                
                return Response(
                    {"message": "Submission deleted successfully"},
                    status=status.HTTP_200_OK
                )
        except PatientSubmission.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="Submission not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AdminUserDeleteView(APIView):
    """
    Admin user deletion endpoint.
    
    DELETE /api/v1/admin/users/{id}/
    Deletes a user (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def delete(self, request, user_id):
        """Delete a user (admin only)."""
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(id=user_id)
                user_email = user.email
                user.delete()
                
                log_action(
                    actor=request.user,
                    action_type="USER_DELETED",
                    target_description=f"User {user_email} account erased",
                    justification=request.data.get('justification', 'No justification provided')
                )
                
                return Response(
                    {"message": "User deleted successfully"},
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

class AuditLogListView(APIView):
    """
    Admin audit log listing endpoint.
    
    GET /api/v1/admin/audit-logs/
    Returns all audit logs (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """List all audit logs in the system (admin only)."""
        logs = AuditLog.objects.all().order_by('-timestamp')
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminUserSuspendView(APIView):
    """
    Admin user suspension endpoint.
    
    PATCH /api/v1/admin/users/{id}/suspend/
    Suspends or unsuspends a user account (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
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
                user = User.objects.select_for_update().get(id=user_id)
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

class SystemConfigView(APIView):
    """
    Admin system configuration endpoint.
    
    GET /api/v1/admin/config/
    PATCH /api/v1/admin/config/
    Manages global system settings (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """List all system configurations."""
        configs = SystemConfig.objects.all()
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
                config, created = SystemConfig.objects.select_for_update().get_or_create(key=key)
                old_value = config.value
                config.value = value
                config.updated_by = request.user
                config.save()
                
                log_action(
                    actor=request.user,
                    action_type="CONFIG_UPDATE",
                    target_description=f"System config '{key}' updated",
                    metadata={"old_value": old_value, "new_value": value}
                )
                
                return Response(
                    {"message": f"Config '{key}' updated successfully"},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminReportExportView(APIView):
    """
    Admin report export endpoint.
    
    GET /api/v1/admin/reports/export/
    Generates a CSV summary of patient throughput (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        """Export system metrics as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="triagesync_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Patient', 'Condition', 'Priority', 'Status', 'Wait Time (mins)', 'Created At'])
        
        submissions = PatientSubmission.objects.all().order_by('-created_at')
        
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
