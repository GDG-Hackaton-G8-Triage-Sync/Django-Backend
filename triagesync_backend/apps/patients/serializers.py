from rest_framework import serializers
from .models import PatientSubmission, StaffNote, VitalsLog

class StaffNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = StaffNote
        fields = ['id', 'author_name', 'content', 'is_internal', 'created_at']
        read_only_fields = ['id', 'author_name', 'created_at']


class VitalsLogSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)

    class Meta:
        model = VitalsLog
        fields = [
            'id', 'recorded_by_name', 'systolic_bp', 'diastolic_bp', 
            'heart_rate', 'temperature_c', 'respiratory_rate', 
            'oxygen_saturation', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_by_name', 'recorded_at']

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
        fields = ['id', 'patient', 'symptoms', 'priority', 'urgency_score', 'condition', 'status', 'photo_name', 'created_at', 'processed_at', 'verified_by_user', 'verified_at']
        read_only_fields = fields


class TriageSubmissionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for triage submission history retrieval.
    Used by TriageSubmissionsHistoryView for GET /api/v1/triage-submissions/
    
    All fields are read-only as this is a GET-only endpoint.
    Includes patient_email field that pulls from patient.user.email relationship.
    """
    patient_email = serializers.EmailField(source='patient.user.email', read_only=True)
    
    class Meta:
        model = PatientSubmission
        fields = [
            'id',
            'patient_email',
            'symptoms',
            'priority',
            'urgency_score',
            'condition',
            'status',
            'created_at',
            'processed_at'
        ]
        read_only_fields = fields