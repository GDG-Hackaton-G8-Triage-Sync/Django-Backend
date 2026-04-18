from django.db import models


class TriageSession(models.Model):
    session_id = models.CharField(max_length=20)
    symptoms = models.TextField()
    status = models.CharField(max_length=20)
    urgency_score = models.IntegerField(null=True, blank=True)
    priority_level = models.IntegerField(null=True, blank=True)
    queue_position = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session_id
