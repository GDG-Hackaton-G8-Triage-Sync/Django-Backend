from django.conf import settings
from django.db import models


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile"
    )
    # required feilds
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    contact_info = models.CharField(max_length=255, blank=True)
    
    gender = models.CharField(max_length=50, default="Male")
    age = models.IntegerField(default=18)
    blood_type = models.CharField(max_length=10, default="O+")

    # Additional profile fields for generic profile endpoint
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
    photo = models.FileField(upload_to="triage_photos/", null=True, blank=True)

    # TRIAGE OUTPUT
    priority = models.IntegerField(null=True, blank=True)
    urgency_score = models.IntegerField(null=True, blank=True)
    condition = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    is_critical = models.BooleanField(default=False)
    explanation = models.JSONField(default=list, blank=True)
    recommended_action = models.TextField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)
    
    # ROUTING AND FILTERING FIELDS (underutilized-features-implementation)
    requires_immediate_attention = models.BooleanField(default=False)
    specialist_referral_suggested = models.BooleanField(default=False)
    critical_keywords = models.JSONField(default=list, blank=True)

    # WORKFLOW
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )

    # STAFF ACTIONS
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_submissions"
    )
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

    # METADATA (for tracking SLA alerts and other system state)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Submission {self.id} by {self.patient.name}"


class StaffNote(models.Model):
    submission = models.ForeignKey(PatientSubmission, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class VitalsLog(models.Model):
    submission = models.ForeignKey(PatientSubmission, on_delete=models.CASCADE, related_name="vitals_history")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.IntegerField(null=True, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

