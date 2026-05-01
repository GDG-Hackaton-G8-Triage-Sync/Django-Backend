from rest_framework import serializers
from triagesync_backend.apps.authentication.models import User
from .models import AuditLog, SystemConfig

class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin user listing.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'date_joined', 'is_active']
        read_only_fields = fields

class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'timestamp', 'actor_name', 'action_type', 'target_description', 'justification', 'metadata']

class RoleUpdateSerializer(serializers.Serializer):
    """
    Serializer for admin role updates.
    """
    role = serializers.ChoiceField(
        choices=['patient', 'nurse', 'doctor', 'admin', 'staff'],
        required=True
    )
