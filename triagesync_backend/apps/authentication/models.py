from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        PATIENT = "patient", "Patient"
        NURSE = "nurse", "Nurse"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
