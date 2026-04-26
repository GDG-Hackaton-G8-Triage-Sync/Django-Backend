from rest_framework import serializers

from .models import PatientSubmission


class PatientSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientSubmission
        fields = ("id", "patient", "symptoms", "created_at")
        read_only_fields = ("id", "created_at")
