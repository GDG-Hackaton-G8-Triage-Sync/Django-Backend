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
    
    # Additional profile fields for generic profile endpoint
    gender = models.CharField(max_length=50, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    blood_type = models.CharField(max_length=10, blank=True, null=True)
    health_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    bad_habits = models.TextField(blank=True, null=True)

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
    verified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_submissions"
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Submission {self.id} by {self.patient.name}"
