from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    Notification model for storing user notifications.
    
    Stores persistent notifications that can be delivered via REST API
    and real-time via WebSocket connections.
    """
    
    class NotificationType(models.TextChoices):
        """Enumeration of all supported notification types."""
        TRIAGE_STATUS_CHANGE = "triage_status_change", "Triage Status Change"
        PRIORITY_UPDATE = "priority_update", "Priority Update"
        ROLE_CHANGE = "role_change", "Role Change"
        CRITICAL_ALERT = "critical_alert", "Critical Alert"
        SYSTEM_MESSAGE = "system_message", "System Message"
    
    # Primary key field
    id = models.BigAutoField(primary_key=True)
    
    # User relationship
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
        help_text="The user who should receive this notification"
    )
    
    # Notification content fields
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
        help_text="The type of notification"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Short title for the notification (1-200 characters)"
    )
    
    message = models.CharField(
        max_length=1000,
        help_text="Detailed message content (1-1000 characters)"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional structured data related to the notification"
    )
    
    # Status and timestamp fields
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the user has read this notification"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the notification was created"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was marked as read"
    )
    
    class Meta:
        app_label = "notifications"
        db_table = "notifications"
        ordering = ["-created_at"]  # Newest first
        indexes = [
            # Composite index for efficient user-specific queries with date ordering
            models.Index(fields=["user", "created_at"], name="idx_notifications_user_created"),
            # Composite index for efficient filtering by read status per user
            models.Index(fields=["user", "is_read"], name="idx_notifications_user_read"),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark this notification as read if not already read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(models.Model):
    """
    User preferences for notification types.
    
    Controls which notification types a user wants to receive.
    All types default to enabled (opt-out model).
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        help_text="The user these preferences belong to"
    )
    
    # Individual preference fields for each notification type
    triage_status_change_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications when triage status changes"
    )
    
    priority_update_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications when priority is updated"
    )
    
    role_change_enabled = models.BooleanField(
        default=True,
        help_text="Receive notifications when role changes"
    )
    
    critical_alert_enabled = models.BooleanField(
        default=True,
        help_text="Receive critical alert notifications"
    )
    
    system_message_enabled = models.BooleanField(
        default=True,
        help_text="Receive system message notifications"
    )
    
    class Meta:
        app_label = "notifications"
        db_table = "notification_preferences"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    def is_enabled(self, notification_type: str) -> bool:
        """
        Check if a specific notification type is enabled for this user.
        
        Args:
            notification_type: One of Notification.NotificationType values
            
        Returns:
            True if the notification type is enabled, False otherwise
        """
        field_name = f"{notification_type}_enabled"
        return getattr(self, field_name, True)