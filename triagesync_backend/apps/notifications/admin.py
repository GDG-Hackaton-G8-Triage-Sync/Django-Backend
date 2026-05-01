from django.contrib import admin
from .models import Notification, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "user__email")
    readonly_fields = ("created_at", "read_at")
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Recipient & Meta", {
            "fields": ("user", "notification_type", "is_read", "read_at")
        }),
        ("Content", {
            "fields": ("title", "message", "metadata")
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "triage_status_change_enabled", "priority_update_enabled", "critical_alert_enabled")
    search_fields = ("user__username", "user__email")
    
    fieldsets = (
        ("User", {
            "fields": ("user",)
        }),
        ("Channel Preferences", {
            "fields": (
                "triage_status_change_enabled",
                "priority_update_enabled",
                "role_change_enabled",
                "critical_alert_enabled",
                "system_message_enabled"
            )
        }),
    )
