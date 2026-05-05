# Serializer for validating Gemini AI output
from rest_framework import serializers
from triagesync_backend.apps.patients.models import PatientSubmission


class TriageInputSerializer(serializers.Serializer):
    """Simple serializer for triage evaluation (text only)"""
    symptoms = serializers.CharField(required=True, max_length=500)


class TriageAIRequestSerializer(serializers.Serializer):
    """Combined serializer for AI triage (text + optional files)"""
    symptoms = serializers.CharField(required=False, allow_blank=True, help_text="Patient symptoms description")
    prompt = serializers.CharField(required=False, allow_blank=True, help_text="Alternative to symptoms field")
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True)
    blood_type = serializers.CharField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True, help_text="Supplementary PDF document")
    image = serializers.ImageField(required=False, allow_null=True, help_text="Photo of injury/symptom")
    photo = serializers.ImageField(required=False, allow_null=True, help_text="Alternative to image field")


class TriageSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for triage submission responses
    Maps model field "symptoms" to API field "description"
    """
    description = serializers.CharField(source="symptoms")
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    metadata = serializers.JSONField(read_only=True)
    
    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "description",  # API field name
            "priority",
            "recommended_action",
            "urgency_score", 
            "condition",
            "status",
            "metadata",
            "created_at"
        )
        read_only_fields = ("id", "priority", "urgency_score", "condition", "status", "metadata", "created_at")


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
    # Backward-compatible enrichment fields (optional with safe defaults)
    critical_keywords = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        allow_empty=True,
    )
    requires_immediate_attention = serializers.BooleanField(required=False, default=False)
    specialist_referral_suggested = serializers.BooleanField(required=False, default=False)


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
