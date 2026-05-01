# Serializer for validating Gemini AI output
from rest_framework import serializers
from triagesync_backend.apps.patients.models import PatientSubmission


class TriageUserInputSerializer(serializers.Serializer):
    """User input serializer: expects symptoms, age, gender as separate fields"""
    symptoms = serializers.CharField(required=True)
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True)


class TriageSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for triage submission responses
    Maps model field "symptoms" to API field "description"
    """
    description = serializers.CharField(source="symptoms")
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ')
    
    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "description",  # API field name
            "priority",
            "urgency_score", 
            "condition",
            "status",
            "photo_name",
            "created_at"
        )


class TriageAIResponseSerializer(serializers.Serializer):
    """Serializer for AI triage response validation"""
    priority_level = serializers.IntegerField(min_value=1, max_value=5)
    urgency_score = serializers.IntegerField(min_value=0, max_value=100)
    condition = serializers.CharField()
    category = serializers.ChoiceField(choices=["Cardiac", "Respiratory", "Trauma", "Neurological", "General"])
    is_critical = serializers.BooleanField()
    explanation = serializers.ListField(child=serializers.CharField(), min_length=1)
    recommended_action = serializers.CharField()
    reason = serializers.CharField()


class PDFUploadSerializer(serializers.Serializer):
    """PDF upload serializer (5MB limit)"""
    file = serializers.FileField()

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("File size must be under 5MB.")
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return value
