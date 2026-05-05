from rest_framework import serializers

class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)

class SuccessMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
