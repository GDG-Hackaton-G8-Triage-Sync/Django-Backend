from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        PATIENT = "patient", "Patient"
        NURSE = "nurse", "Nurse"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PATIENT
    )

    def is_doctor(self):
        return self.role == self.Roles.DOCTOR

    def is_nurse(self):
        return self.role == self.Roles.NURSE

    def is_admin(self):
        return self.role == self.Roles.ADMIN

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
