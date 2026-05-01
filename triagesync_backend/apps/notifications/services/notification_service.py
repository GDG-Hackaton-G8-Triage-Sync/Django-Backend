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
