from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    
    Provides consistent serialization for both REST API responses and WebSocket messages.
    Includes validation for all notification fields according to business rules.
    
    Requirements: 3.6, 12.1, 12.2, 12.3, 12.5, 12.6, 12.7
    """
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "metadata",
            "is_read",
            "created_at",
            "read_at"
        ]
        read_only_fields = ["id", "created_at", "read_at"]
    
    def validate_notification_type(self, value):
        """
        Validate that notification_type is one of the allowed enum values.
        
        Requirements: 12.5
        """
        if value not in Notification.NotificationType.values:
            raise serializers.ValidationError(
                f"Invalid notification type. Must be one of: {', '.join(Notification.NotificationType.values)}"
            )
        return value
    
    def validate_title(self, value):
        """
        Validate that title is between 1 and 200 characters.
        
        Requirements: 12.6
        """
        if not value or len(value) < 1 or len(value) > 200:
            raise serializers.ValidationError("Title must be between 1 and 200 characters")
        return value
    
    def validate_message(self, value):
        """
        Validate that message is between 1 and 1000 characters.
        
        Requirements: 12.7
        """
        if not value or len(value) < 1 or len(value) > 1000:
            raise serializers.ValidationError("Message must be between 1 and 1000 characters")
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    
    Handles user notification preferences for all notification types.
    All fields are optional to support partial updates.
    
    Requirements: 8.4, 8.5
    """
    
    class Meta:
        model = NotificationPreference
        fields = [
            "triage_status_change_enabled",
            "priority_update_enabled",
            "role_change_enabled",
            "critical_alert_enabled",
            "system_message_enabled"
        ]