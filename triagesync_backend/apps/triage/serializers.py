# Serializer for validating Gemini AI output
from rest_framework import serializers
from .models import TriageResult
class TriageAIResponseSerializer(serializers.Serializer):
    priority = serializers.ChoiceField(choices=["high", "medium", "low"], required=False)
    priority_level = serializers.IntegerField(min_value=1, max_value=5, required=False)
    urgency_score = serializers.IntegerField(min_value=0, max_value=100, required=False)
    reason = serializers.CharField()
    recommended_action = serializers.CharField()


class TriageResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageResult
        fields = ("id", "priority", "explanation", "created_at")
