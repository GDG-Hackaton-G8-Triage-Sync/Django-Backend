from rest_framework import serializers
from triagesync_backend.apps.patients.models import PatientSubmission


class DashboardPatientSerializer(serializers.ModelSerializer):
    # 🔁 Rename fields to match API contract
    description = serializers.CharField(source="symptoms")
    patient_name = serializers.CharField(source="patient.name")
    category = serializers.SerializerMethodField()
    wait_time_minutes = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()
    reason_summary = serializers.SerializerMethodField()

    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "patient_name",
            "description",
            "priority",
            "urgency_score",
            "condition",
            "category",
            "status",
            "verified_by_user",
            "verified_at",
            "created_at",
            "wait_time_minutes",
            "sla_status",
            "reason_summary",
        )
    
    def get_category(self, obj):
        """Return category or 'General' if null."""
        return obj.category if obj.category else "General"
    
    def get_wait_time_minutes(self, obj):
        """
        Calculate wait time using wait_time_service.
        
        Requirements: 4.5
        """
        from .services.wait_time_service import calculate_wait_time
        return calculate_wait_time(obj)
    
    def get_sla_status(self, obj):
        """
        Get SLA status using wait_time_service.
        
        Requirements: 5.1
        """
        from .services.wait_time_service import calculate_wait_time, get_sla_status
        wait_time = calculate_wait_time(obj)
        return get_sla_status(wait_time)
    
    def get_reason_summary(self, obj):
        """
        Return truncated AI reason for list view (100 chars).
        
        Returns empty string if reason is null or empty.
        Appends "..." if truncated.
        
        Requirements: 11.1, 11.2, 11.3, 11.4
        """
        if not obj.reason:
            return ""
        return obj.reason[:100] + "..." if len(obj.reason) > 100 else obj.reason


class PatientDetailSerializer(serializers.ModelSerializer):
    """
    Extended serializer for patient detail view with full AI reason.
    
    Requirements: 9.1, 9.2, 9.3, 9.4
    """
    description = serializers.CharField(source="symptoms")
    patient_name = serializers.CharField(source="patient.name")
    category = serializers.SerializerMethodField()
    wait_time_minutes = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()
    reason_full = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientSubmission
        fields = (
            "id",
            "patient_name",
            "description",
            "priority",
            "urgency_score",
            "condition",
            "category",
            "status",
            "verified_by_user",
            "verified_at",
            "created_at",
            "processed_at",
            "wait_time_minutes",
            "sla_status",
            "reason_full",
            "explanation",
            "recommended_action",
        )
    
    def get_category(self, obj):
        """Return category or 'General' if null."""
        return obj.category if obj.category else "General"
    
    def get_wait_time_minutes(self, obj):
        """
        Calculate wait time using wait_time_service.
        
        Requirements: 4.5
        """
        from .services.wait_time_service import calculate_wait_time
        return calculate_wait_time(obj)
    
    def get_sla_status(self, obj):
        """
        Get SLA status using wait_time_service.
        
        Requirements: 5.1
        """
        from .services.wait_time_service import calculate_wait_time, get_sla_status
        wait_time = calculate_wait_time(obj)
        return get_sla_status(wait_time)
    
    def get_reason_full(self, obj):
        """
        Return full AI reasoning with default text if null/empty.
        
        Requirements: 9.3, 9.4
        """
        if not obj.reason:
            return "No reasoning provided"
        return obj.reason

class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=PatientSubmission.Status.choices, required=True)

class PriorityUpdateSerializer(serializers.Serializer):
    priority = serializers.IntegerField(min_value=1, max_value=5, required=True)
