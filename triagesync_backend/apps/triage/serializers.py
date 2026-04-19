# Serializer for validating Gemini AI output
from rest_framework import serializers
from .models import TriageResult


# If you have an input serializer for user data, vital_signs should be optional.
# Here is an example input serializer with optional vital_signs:
class TriageUserInputSerializer(serializers.Serializer):
    symptoms = serializers.ListField(child=serializers.CharField(), required=True)
    # All other fields (age, gender, medical_history, vital_signs) will be fetched from the database during patient registration, not from user input or AI for now.

class TriageAIResponseSerializer(serializers.Serializer):
    priority_level = serializers.IntegerField(min_value=1, max_value=5)
    urgency_score = serializers.IntegerField(min_value=0, max_value=100)
    condition = serializers.CharField()
    category = serializers.ChoiceField(choices=["Cardiac", "Respiratory", "Trauma", "Neurological", "General"])
    is_critical = serializers.BooleanField()
    explanation = serializers.ListField(child=serializers.CharField(), min_length=1)
    # priority (string) is ignored if present in the AI response


class TriageResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageResult
        fields = ("id", "priority", "explanation", "created_at")
