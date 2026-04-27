from rest_framework import serializers

from .models import PatientSubmission

class TriageSubmissionSerializer(serializers.Serializer):
    symptoms = serializers.CharField(max_length=500)
    language = serializers.CharField(default="en", required=False)
    attachments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

    def validate_symptoms(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Symptoms cannot be empty.")
        return value
    
    
class PatientSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientSubmission
        fields = ("id", "patient", "symptoms", "created_at")
        read_only_fields = ("id", "created_at")
