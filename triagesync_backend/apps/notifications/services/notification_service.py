import logging
from django.utils import timezone
from django.db import transaction
from triagesync_backend.apps.notifications.models import Notification, NotificationPreference
from triagesync_backend.apps.notifications.serializers import NotificationSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class NotificationService:
    @classmethod
    def create_notification(cls, user, notification_type, title, message, metadata=None):
        if not cls._should_send_notification(user, notification_type):
            return None
        if notification_type not in Notification.NotificationType.values:
            raise ValueError(f"Invalid notification_type: {notification_type}")
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                metadata=metadata or {},
                is_read=False,
                created_at=timezone.now(),
            )
            cls._deliver_realtime(notification)
            return notification

    @classmethod
    def _should_send_notification(cls, user, notification_type):
        try:
            pref = NotificationPreference.objects.get(user=user)
            field = f"{notification_type}_enabled"
            return getattr(pref, field, True)
        except NotificationPreference.DoesNotExist:
            return True

    @classmethod
    def _deliver_realtime(cls, notification):
        try:
            channel_layer = get_channel_layer()
            group_name = f"user_{notification.user.id}"
            serializer = NotificationSerializer(notification)
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_message",
                    "notification": serializer.data,
                }
            )
        except Exception as e:
            logging.error(f"WebSocket delivery failed: {e}")

    @classmethod
    def create_bulk_notifications(cls, users, notification_type, title, message, metadata=None):
        count = 0
        for user in users:
            if cls.create_notification(user, notification_type, title, message, metadata):
                count += 1
        return count

    @classmethod
    def create_sla_alert(cls, submission, alert_type):
        """
        Create SLA breach alert notification.
        
        Args:
            submission: PatientSubmission instance
            alert_type: 'warning' (25min) or 'critical' (30min)
        """
        from triagesync_backend.apps.dashboard.services.wait_time_service import calculate_wait_time
        from triagesync_backend.apps.authentication.models import User
        
        wait_time = calculate_wait_time(submission)
        
        # Determine notification type and message based on alert type
        if alert_type == 'warning':
            title = f"SLA Warning: Patient {submission.patient.name}"
            message = f"Patient has been waiting {wait_time:.1f} minutes (approaching 30min SLA). "
            notification_type = Notification.NotificationType.SYSTEM_MESSAGE
        else:  # critical
            title = f"SLA BREACH: Patient {submission.patient.name}"
            message = f"Patient has exceeded 30-minute SLA ({wait_time:.1f} minutes). "
            notification_type = Notification.NotificationType.CRITICAL_ALERT
        
        # Truncate AI reason to 200 characters for notification message
        if submission.reason:
            reason_truncated = submission.reason[:200] + "..." if len(submission.reason) > 200 else submission.reason
            message += f"AI Reason: {reason_truncated}"
        else:
            reason_truncated = None
        
        # Build metadata with full AI reason and submission details
        metadata = {
            'submission_id': submission.id,
            'wait_time_minutes': wait_time,
            'priority': submission.priority,
            'patient_name': submission.patient.name,
            'category': submission.category or 'General',
            'ai_reason': reason_truncated,
            'ai_reason_full': submission.reason,  # Full reason in metadata
        }
        
        # Determine recipients based on alert type
        if alert_type == 'critical':
            # Send to all staff users (nurses, doctors, admins)
            staff_users = User.objects.filter(
                role__in=[User.Roles.NURSE, User.Roles.DOCTOR, User.Roles.ADMIN]
            )
        else:  # warning
            # Send to assigned staff only, or all staff if not assigned
            if submission.assigned_to:
                staff_users = [submission.assigned_to]
            else:
                staff_users = User.objects.filter(
                    role__in=[User.Roles.NURSE, User.Roles.DOCTOR, User.Roles.ADMIN]
                )
        
        # Create notifications for all target users
        return cls.create_bulk_notifications(
            users=staff_users,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata
        )
