from django.conf import settings
from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=100)
    symptoms = models.TextField()
    priority = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Submission {self.id} by {self.patient_id}"
