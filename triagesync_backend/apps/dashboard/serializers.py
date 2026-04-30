from rest_framework import serializers

from triagesync_backend.apps.patients.models import PatientSubmission
from triagesync_backend.apps.patients.serializers import VitalsLogSerializer


class DashboardPatientSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="symptoms", read_only=True)
    patient_id = serializers.IntegerField(source="patient.id", read_only=True)
    patient_user_id = serializers.IntegerField(source="patient.user.id", read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_email = serializers.EmailField(source="patient.user.email", read_only=True)
    age = serializers.IntegerField(source="patient.age", read_only=True)
    gender = serializers.CharField(source="patient.gender", read_only=True)
    blood_type = serializers.CharField(source="patient.blood_type", read_only=True)
    health_history = serializers.CharField(source="patient.health_history", read_only=True)
    allergies = serializers.CharField(source="patient.allergies", read_only=True)
    current_medications = serializers.CharField(source="patient.current_medications", read_only=True)
    bad_habits = serializers.CharField(source="patient.bad_habits", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by_user.username", read_only=True)
    reasoning = serializers.CharField(source="reason", read_only=True)
    vitals = VitalsLogSerializer(many=True, read_only=True)
    photo_url = serializers.SerializerMethodField()
    confidence = serializers.FloatField(read_only=True)

    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "patient_id",
            "patient_user_id",
            "patient_name",
            "patient_email",
            "description",
            "priority",
            "urgency_score",
            "condition",
            "category",
            "status",
            "is_critical",
            "photo_name",
            "photo_url",
            "age",
            "gender",
            "blood_type",
            "health_history",
            "allergies",
            "current_medications",
            "bad_habits",
            "explanation",
            "recommended_action",
            "reason",
            "reasoning",
            "confidence",
            "source",
            "vitals",
            "verified_by_user",
            "verified_by_name",
            "verified_at",
            "created_at",
            "processed_at",
        )

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url
