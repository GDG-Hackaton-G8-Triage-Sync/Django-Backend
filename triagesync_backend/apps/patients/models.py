
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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="submissions")
    symptoms = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class TriageItem(models.Model):
    #  reference
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triage_items"
    )

   
    description = models.TextField(max_length=500)

    priority = models.IntegerField(default=3)  # 1 = high, 3 = low
    urgency_score = models.IntegerField(default=0)

    condition = models.CharField(max_length=255, default="unknown")

    status = models.CharField(
        max_length=20,
        default="processing",
        choices=[
            ("processing", "Processing"),
            ("waiting", "Waiting"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ]
    )

    #  Required timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Staff actions 
    verified_by = models.CharField(max_length=255, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TriageItem {self.id} - {self.priority} - {self.urgency_score}"
