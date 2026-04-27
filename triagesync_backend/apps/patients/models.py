from django.conf import settings
from django.db import models


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile"
    )
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    contact_info = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class PatientSubmission(models.Model):

    class Status(models.TextChoices):
        WAITING = "waiting"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="submissions")

    # INPUT
    symptoms = models.TextField()
    photo_name = models.CharField(max_length=255, null=True, blank=True)

    # TRIAGE OUTPUT
    priority = models.IntegerField(null=True, blank=True)
    urgency_score = models.IntegerField(null=True, blank=True)
    condition = models.CharField(max_length=255, null=True, blank=True)

    # WORKFLOW
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    # STAFF ACTIONS
    verified_by = models.CharField(max_length=255, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Submission {self.id} by {self.patient.name}"
