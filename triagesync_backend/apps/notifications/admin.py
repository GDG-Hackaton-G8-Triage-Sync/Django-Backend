from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "notification_type",
        "title",
        "is_read",
        "created_at",
        "read_at",
    )
    search_fields = ("user__username", "user__email", "title", "message")
    list_filter = ("notification_type", "is_read", "created_at")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "read_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "triage_status_change_enabled",
        "priority_update_enabled",
        "role_change_enabled",
        "critical_alert_enabled",
        "system_message_enabled",
    )
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
