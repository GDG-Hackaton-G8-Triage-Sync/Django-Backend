"""
Patient Service - Handles patient submission status updates with notifications
"""
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from triagesync_backend.apps.patients.models import PatientSubmission
from triagesync_backend.apps.notifications.services.notification_service import NotificationService
from triagesync_backend.apps.realtime.services.broadcast_service import (
    broadcast_status_changed,
    broadcast_queue_snapshot,
)

User = get_user_model()
logger = logging.getLogger("patients.service")


class PatientService:
    """Service for managing patient submissions and status updates."""
    
    @classmethod
    def update_submission_status(cls, submission_id: int, new_status: str, staff_user=None):
        """
        Update patient submission status and send appropriate notifications.
        
        Args:
            submission_id: ID of the PatientSubmission to update
            new_status: New status ('waiting', 'in_progress', 'completed')
            staff_user: User making the status change (optional)
        
        Returns:
            Updated PatientSubmission instance
        """
        try:
            submission = PatientSubmission.objects.select_related('patient__user').get(id=submission_id)
            old_status = submission.status
            
            # Update status
            submission.status = new_status
            if new_status == 'in_progress' and not submission.processed_at:
                submission.processed_at = timezone.now()
            if staff_user:
                submission.verified_by_user = staff_user
                submission.verified_at = timezone.now()
            
            submission.save()
            
            # Broadcast real-time status change
            broadcast_status_changed(submission.id, new_status)
            # Update full queue snapshot for patient and staff
            try:
                broadcast_queue_snapshot(submission.id)
            except Exception:
                # Best-effort only; do not fail the status update
                logger.debug(f"Failed to broadcast queue snapshot for submission {submission.id}")
            
            # Send notifications
            cls._send_status_change_notifications(submission, old_status, new_status, staff_user)
            
            logger.info(f"Submission {submission_id} status updated from {old_status} to {new_status}")
            return submission
            
        except PatientSubmission.DoesNotExist:
            logger.error(f"Submission {submission_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to update submission {submission_id} status: {str(e)}")
            raise
    
    @classmethod
    def _send_status_change_notifications(cls, submission, old_status, new_status, staff_user):
        """Send notifications for status changes."""
        try:
            patient_user = submission.patient.user
            
            # Notification messages based on status
            status_messages = {
                'in_progress': {
                    'title': 'Your Case is Being Reviewed',
                    'message': f'Medical staff are now reviewing your triage submission (ID: {submission.id}). You will be notified when the review is complete.',
                },
                'completed': {
                    'title': 'Triage Review Complete',
                    'message': f'Your triage submission (ID: {submission.id}) has been completed. Please check with medical staff for next steps.',
                },
                'waiting': {
                    'title': 'Case Status Updated',
                    'message': f'Your triage submission (ID: {submission.id}) status has been updated to waiting.',
                }
            }
            
            # Notify patient about status change
            if new_status in status_messages:
                NotificationService.create_notification(
                    user=patient_user,
                    notification_type="triage_status_change",
                    title=status_messages[new_status]['title'],
                    message=status_messages[new_status]['message'],
                    metadata={
                        "submission_id": submission.id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "priority": submission.priority,
                        "condition": submission.condition,
                        "staff_user_id": staff_user.id if staff_user else None,
                        "action_type": "status_change"
                    }
                )
            
            # Notify supervisors about completed high-priority cases
            if new_status == 'completed' and submission.priority <= 2:
                supervisors = User.objects.filter(role="supervisor")
                NotificationService.create_bulk_notifications(
                    users=supervisors,
                    notification_type="system_message",
                    title="High Priority Case Completed",
                    message=f"Priority {submission.priority} case (ID: {submission.id}) has been completed by staff.",
                    metadata={
                        "submission_id": submission.id,
                        "priority": submission.priority,
                        "condition": submission.condition,
                        "completed_by": staff_user.id if staff_user else None,
                        "action_type": "high_priority_completion"
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to send status change notifications for submission {submission.id}: {str(e)}")
    
    @classmethod
    def assign_staff_to_submission(cls, submission_id: int, staff_user):
        """
        Assign staff member to a patient submission.
        
        Args:
            submission_id: ID of the PatientSubmission
            staff_user: User to assign to the submission
        """
        try:
            submission = PatientSubmission.objects.select_related('patient__user').get(id=submission_id)
            
            # Update assignment
            submission.verified_by_user = staff_user
            submission.verified_at = timezone.now()
            
            # If not already in progress, update status
            if submission.status == 'waiting':
                submission.status = 'in_progress'
                submission.processed_at = timezone.now()
            
            submission.save()
            
            # Notify patient about assignment
            NotificationService.create_notification(
                user=submission.patient.user,
                notification_type="triage_status_change",
                title="Medical Staff Assigned",
                message=f"Medical staff has been assigned to your case (ID: {submission.id}) and will begin review shortly.",
                metadata={
                    "submission_id": submission.id,
                    "assigned_staff_id": staff_user.id,
                    "priority": submission.priority,
                    "condition": submission.condition,
                    "action_type": "staff_assignment"
                }
            )
            
            # Notify assigned staff
            NotificationService.create_notification(
                user=staff_user,
                notification_type="system_message",
                title="New Case Assignment",
                message=f"You have been assigned to patient case ID: {submission.id} (Priority: {submission.priority}, Condition: {submission.condition})",
                metadata={
                    "submission_id": submission.id,
                    "patient_id": submission.patient.id,
                    "priority": submission.priority,
                    "condition": submission.condition,
                    "action_type": "staff_assignment"
                }
            )
            
            logger.info(f"Staff {staff_user.id} assigned to submission {submission_id}")
            return submission
            
        except PatientSubmission.DoesNotExist:
            logger.error(f"Submission {submission_id} not found for assignment")
            raise
        except Exception as e:
            logger.error(f"Failed to assign staff to submission {submission_id}: {str(e)}")
            raise