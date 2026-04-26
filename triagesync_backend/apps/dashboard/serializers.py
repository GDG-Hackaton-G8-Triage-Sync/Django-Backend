from rest_framework import serializers

from triagesync_backend.apps.patients.models import PatientSubmission


class DashboardPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientSubmission
        fields = ("id", "patient", "symptoms", "created_at")
