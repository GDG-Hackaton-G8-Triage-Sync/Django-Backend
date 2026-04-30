"""
System Notification Service - Handles system-wide notifications and alerts
"""
import logging
from django.contrib.auth import get_user_model
from triagesync_backend.apps.notifications.services.notification_service import NotificationService

User = get_user_model()
logger = logging.getLogger("notifications.system")


class SystemNotificationService:
    """Service for sending system-wide notifications and administrative alerts."""
    
    @classmethod
    def send_system_maintenance_alert(cls, message: str, affected_roles=None):
        """
        Send system maintenance notification to all users or specific roles.
        
        Args:
            message: Maintenance message to send
            affected_roles: List of roles to notify (None = all users)
        """
        try:
            if affected_roles:
                users = User.objects.filter(role__in=affected_roles)
            else:
                users = User.objects.all()
            
            count = NotificationService.create_bulk_notifications(
                users=users,
                notification_type="system_message",
                title="System Maintenance Notice",
                message=message,
                metadata={
                    "alert_type": "maintenance",
                    "affected_roles": affected_roles or ["all"]
                }
            )
            
            logger.info(f"System maintenance alert sent to {count} users")
            return count
            
        except Exception as e:
            logger.error(f"Failed to send system maintenance alert: {str(e)}")
            raise
    
    @classmethod
    def send_emergency_broadcast(cls, title: str, message: str, priority_roles=None):
        """
        Send emergency broadcast to all staff or priority roles.
        
        Args:
            title: Emergency alert title
            message: Emergency message
            priority_roles: Roles to prioritize (default: supervisors, doctors)
        """
        try:
            if priority_roles is None:
                priority_roles = ["admin", "doctor", "staff"]
            
            # Send to priority roles first
            priority_users = User.objects.filter(role__in=priority_roles)
            priority_count = NotificationService.create_bulk_notifications(
                users=priority_users,
                notification_type="critical_alert",
                title=f"EMERGENCY: {title}",
                message=message,
                metadata={
                    "alert_type": "emergency_broadcast",
                    "priority_notification": True
                }
            )
            
            # Send to all other staff
            other_staff = User.objects.filter(role__in=["nurse"]).exclude(role__in=priority_roles)
            other_count = NotificationService.create_bulk_notifications(
                users=other_staff,
                notification_type="critical_alert",
                title=f"ALERT: {title}",
                message=message,
                metadata={
                    "alert_type": "emergency_broadcast",
                    "priority_notification": False
                }
            )
            
            total_count = priority_count + other_count
            logger.info(f"Emergency broadcast sent to {total_count} staff members")
            return total_count
            
        except Exception as e:
            logger.error(f"Failed to send emergency broadcast: {str(e)}")
            raise
    
    @classmethod
    def send_shift_change_notifications(cls, incoming_staff, outgoing_staff, shift_info):
        """
        Send notifications for shift changes.
        
        Args:
            incoming_staff: List of users starting shift
            outgoing_staff: List of users ending shift
            shift_info: Dictionary with shift details
        """
        try:
            # Notify incoming staff
            for staff in incoming_staff:
                NotificationService.create_notification(
                    user=staff,
                    notification_type="system_message",
                    title="Shift Starting",
                    message=f"Your shift is starting. Please check the dashboard for current patient queue and priority cases.",
                    metadata={
                        "shift_type": shift_info.get("type", "regular"),
                        "shift_start": shift_info.get("start_time"),
                        "action_type": "shift_start"
                    }
                )
            
            # Notify outgoing staff
            for staff in outgoing_staff:
                NotificationService.create_notification(
                    user=staff,
                    notification_type="system_message",
                    title="Shift Ending",
                    message=f"Your shift is ending. Please ensure all assigned cases are properly handed over.",
                    metadata={
                        "shift_type": shift_info.get("type", "regular"),
                        "shift_end": shift_info.get("end_time"),
                        "action_type": "shift_end"
                    }
                )
            
            logger.info(f"Shift change notifications sent to {len(incoming_staff + outgoing_staff)} staff")
            
        except Exception as e:
            logger.error(f"Failed to send shift change notifications: {str(e)}")
    
    @classmethod
    def send_queue_overflow_alert(cls, queue_size: int, threshold: int):
        """
        Send alert when patient queue exceeds threshold.
        
        Args:
            queue_size: Current queue size
            threshold: Queue size threshold that was exceeded
        """
        try:
            supervisors = User.objects.filter(role="admin")
            
            NotificationService.create_bulk_notifications(
                users=supervisors,
                notification_type="critical_alert",
                title="Patient Queue Overflow",
                message=f"Patient queue has reached {queue_size} cases, exceeding the threshold of {threshold}. Additional staff may be needed.",
                metadata={
                    "queue_size": queue_size,
                    "threshold": threshold,
                    "alert_type": "queue_overflow"
                }
            )
            
            logger.warning(f"Queue overflow alert sent - Size: {queue_size}, Threshold: {threshold}")
            
        except Exception as e:
            logger.error(f"Failed to send queue overflow alert: {str(e)}")
    
    @classmethod
    def send_role_change_notification(cls, user, old_role: str, new_role: str, changed_by=None):
        """
        Send notification when user role is changed.
        
        Args:
            user: User whose role was changed
            old_role: Previous role
            new_role: New role
            changed_by: User who made the change (optional)
        """
        try:
            # Notify the user about their role change
            NotificationService.create_notification(
                user=user,
                notification_type="role_change",
                title="Account Role Updated",
                message=f"Your account role has been changed from {old_role} to {new_role}. Your access permissions have been updated accordingly.",
                metadata={
                    "old_role": old_role,
                    "new_role": new_role,
                    "changed_by": changed_by.id if changed_by else None,
                    "action_type": "role_change"
                }
            )
            
            # Notify admins about role changes
            supervisors = User.objects.filter(role="admin").exclude(id=user.id)
            if supervisors.exists():
                NotificationService.create_bulk_notifications(
                    users=supervisors,
                    notification_type="system_message",
                    title="User Role Changed",
                    message=f"User {user.username} role changed from {old_role} to {new_role}.",
                    metadata={
                        "affected_user_id": user.id,
                        "old_role": old_role,
                        "new_role": new_role,
                        "changed_by": changed_by.id if changed_by else None,
                        "action_type": "role_change_admin"
                    }
                )
            
            logger.info(f"Role change notifications sent for user {user.id}: {old_role} -> {new_role}")
            
        except Exception as e:
            logger.error(f"Failed to send role change notifications: {str(e)}")
