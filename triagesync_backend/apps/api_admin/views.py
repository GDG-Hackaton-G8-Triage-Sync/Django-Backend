from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from triagesync_backend.apps.authentication.models import User
from triagesync_backend.apps.authentication.permissions import IsAdmin
from triagesync_backend.apps.notifications.services.system_notification_service import SystemNotificationService
from triagesync_backend.apps.patients.models import Patient, PatientSubmission
from triagesync_backend.apps.core.response import error_response
from .serializers import AdminUserSerializer, RoleUpdateSerializer


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
                old_role = user.role
                user.role = serializer.validated_data['role']
                user.save()

                if user.role == User.Roles.PATIENT:
                    Patient.objects.get_or_create(
                        user=user,
                        defaults={
                            "name": user.first_name or user.username,
                            "age": 18,
                            "gender": "other",
                            "blood_type": "O+",
                        },
                    )

                if old_role != user.role:
                    try:
                        SystemNotificationService.send_role_change_notification(
                            user=user,
                            old_role=old_role,
                            new_role=user.role,
                            changed_by=request.user,
                        )
                    except Exception:
                        pass
                
                return Response(
                    AdminUserSerializer(user).data,
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
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, user_id):
        if request.user.id == user_id:
            return error_response(
                code="VALIDATION_ERROR",
                message="You cannot delete your own admin account",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(id=user_id)
                user.delete()
                return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
