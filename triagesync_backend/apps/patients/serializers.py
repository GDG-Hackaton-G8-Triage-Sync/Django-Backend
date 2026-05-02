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
    # Patient Demographics (Nested)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_age = serializers.IntegerField(source='patient.age', read_only=True)
    patient_gender = serializers.CharField(source='patient.gender', read_only=True)
    patient_blood_type = serializers.CharField(source='patient.blood_type', read_only=True)
    patient_medical_history = serializers.CharField(source='patient.health_history', read_only=True)
    patient_allergies = serializers.CharField(source='patient.allergies', read_only=True)
    patient_medications = serializers.CharField(source='patient.medications', read_only=True)
    patient_lifestyle_habits = serializers.CharField(source='patient.lifestyle_habits', read_only=True)
    
    # Staff Info
    assigned_staff_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    verified_by_name = serializers.CharField(source='verified_by_user.username', read_only=True, allow_null=True)

    class Meta:
        model = PatientSubmission
        fields = [
            'id', 'patient', 'patient_name', 'patient_age', 'patient_gender', 
            'patient_blood_type', 'patient_medical_history', 'patient_allergies', 
            'patient_medications', 'patient_lifestyle_habits',
            'symptoms', 'priority', 'urgency_score', 'condition', 'category',
            'status', 'photo_name', 'is_critical', 'explanation', 'reason', 
            'recommended_action', 'confidence', 'source',
            'assigned_to', 'assigned_staff_name',
            'created_at', 'processed_at', 'verified_by_user', 'verified_by_name', 'verified_at'
        ]
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