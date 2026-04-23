from django.db import models


class TriageResult(models.Model):
    priority = models.CharField(max_length=20)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"TriageResult {self.id} [{self.priority}]"
