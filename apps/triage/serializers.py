from rest_framework import serializers

class TriageInputSerializer(serializers.Serializer):
    symptoms = serializers.CharField()
    age = serializers.IntegerField()
    gender = serializers.CharField()