# Serializer for validating Gemini AI output
from rest_framework import serializers
from .models import TriageResult


# If you have an input serializer for user data, vital_signs should be optional.
# Here is an example input serializer with optional vital_signs:

# User input serializer: expects symptoms, age, gender as separate fields
class TriageUserInputSerializer(serializers.Serializer):
    symptoms = serializers.CharField(required=True)
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True)
    # All other fields (medical_history, vital_signs) are not included in the triage input

class TriageAIResponseSerializer(serializers.Serializer):
    priority_level = serializers.IntegerField(min_value=1, max_value=5)
    urgency_score = serializers.IntegerField(min_value=0, max_value=100)
    condition = serializers.CharField()
    category = serializers.ChoiceField(choices=["Cardiac", "Respiratory", "Trauma", "Neurological", "General"])
    is_critical = serializers.BooleanField()
    explanation = serializers.ListField(child=serializers.CharField(), min_length=1)
    recommended_action = serializers.CharField()
    reason = serializers.CharField()
    # priority (string) is ignored if present in the AI response


class TriageResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageResult
        fields = ("id", "priority", "explanation", "created_at")

# PDF upload serializer (5MB limit)
class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("File size must be under 5MB.")
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return value
