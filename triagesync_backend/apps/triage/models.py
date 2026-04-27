import uuid
from django.conf import settings
from django.db import models


class TriageSession(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="triage_sessions"
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_sessions"
    )
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Core triage fields
    status = models.CharField(max_length=20, default="pending")
    priority_level = models.CharField(max_length=20, default="normal")
    urgency_score = models.IntegerField(default=0)

    # For Nardos’s queries
    symptoms = models.TextField(blank=True)
    queue_position = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TriageSession {self.session_id} ({self.status})"


class AIResult(models.Model):
    triage_session = models.OneToOneField(
        TriageSession,
        on_delete=models.CASCADE,
        related_name="ai_result"
    )
    output_json = models.JSONField()
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
    def __str__(self):
        return f"AIResult for session {self.triage_session.session_id}"


class FileUpload(models.Model):
    triage_session = models.ForeignKey(
        TriageSession,
        on_delete=models.CASCADE,
        related_name="files"
    )
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for session {self.triage_session.session_id}"
