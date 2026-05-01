from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """
    Immputable record of administrative actions.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_audits"
    )
    action_type = models.CharField(max_length=100)  # e.g., USER_DELETED, ROLE_CHANGE
    target_description = models.TextField()        # e.g., "User doc@gmail.com"
    justification = models.TextField(blank=True, null=True)
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_type} by {self.actor} at {self.timestamp}"


class SystemConfig(models.Model):
    """
    Dynamic system configuration settings.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.key}: {self.value}"
