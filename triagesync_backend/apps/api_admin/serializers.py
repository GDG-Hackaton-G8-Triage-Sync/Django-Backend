from rest_framework import serializers
from triagesync_backend.apps.authentication.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin user listing.
    Used by AdminUserListView for GET /api/v1/admin/users/
    
    All fields are read-only as this is a GET-only endpoint.
    
    Requirements: 3.2, 3.3
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'date_joined', 'is_active']
        read_only_fields = fields


class RoleUpdateSerializer(serializers.Serializer):
    """
    Serializer for admin role updates.
    Used by AdminUserRoleUpdateView for PATCH /api/v1/admin/users/{id}/role/
    
    Validates that the role field is present and contains a valid role value.
    
    Requirements: 4.2, 4.3, 4.4, 4.5
    """
    role = serializers.ChoiceField(
        choices=[choice for choice, _ in User.Roles.choices],
        required=True,
        error_messages={
            'required': 'Role field is required',
            'invalid_choice': 'Invalid role value. Must be one of: patient, nurse, doctor, admin, staff'
        }
    )
