from rest_framework import serializers
from apps.patients.models import PatientSubmission


class DashboardPatientSerializer(serializers.ModelSerializer):
    # rename field to match API contract ("description" instead of "symptoms")
    description = serializers.CharField(source="symptoms")

    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "description",
            "priority",
            "urgency_score",
            "condition",
            "status",
            "created_at",
        )