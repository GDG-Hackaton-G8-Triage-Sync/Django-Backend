from django.db import models


class TriageResult(models.Model):
    priority = models.CharField(max_length=20)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"TriageResult {self.id} [{self.priority}]"
from django.db import models
from django.conf import settings


class TriageItem(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    description = models.TextField()

    priority = models.IntegerField(default=3)
    urgency_score = models.IntegerField(default=0)
    condition = models.CharField(max_length=255, default="unknown")

    status = models.CharField(
        max_length=20,
        choices=[
            ("waiting", "Waiting"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ],
        default="waiting"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Triage {self.id} - {self.patient_id}"