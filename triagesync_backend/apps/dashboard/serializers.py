from rest_framework import serializers

from triagesync_backend.apps.patients.models import PatientSubmission


class DashboardPatientSerializer(serializers.ModelSerializer):
    # 🔁 Rename fields to match API contract
    description = serializers.CharField(source="symptoms")
    patient_name = serializers.CharField(source="patient.name")

    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "patient_name",
            "description",
            "priority",
            "urgency_score",
            "condition",
            "status",
            "photo_name",
            "verified_by",
            "verified_at",
            "created_at",
        )