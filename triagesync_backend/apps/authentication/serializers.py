from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    # Public-facing name field (mapped to User.username)
    name = serializers.CharField(max_length=255, required=True)
    # Required demographic field
    age = serializers.IntegerField(min_value=0, max_value=150, required=True)
    # Optional fields (may be provided during registration)
    gender = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    blood_type = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    health_history = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allergies = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    current_medications = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bad_habits = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        # include username because it's the model field; API uses `name` instead
        fields = ['username', 'email', 'password', 'role', 'name', 'age', 'gender', 'blood_type', 'health_history', 'allergies', 'current_medications', 'bad_habits']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False}
        }

    def create(self, validated_data):
        # Map API `name` to User.username
        name = validated_data.pop('name')
        age = validated_data.pop('age')
        gender = validated_data.pop('gender', None)
        blood_type = validated_data.pop('blood_type', None)
        health_history = validated_data.pop('health_history', None)
        allergies = validated_data.pop('allergies', None)
        current_medications = validated_data.pop('current_medications', None)
        bad_habits = validated_data.pop('bad_habits', None)

        validated_data['username'] = name
        user = User.objects.create_user(**validated_data)

        # Create or update Patient profile for patient role
        if user.role == 'patient':
            from triagesync_backend.apps.patients.models import Patient
            Patient.objects.create(
                user=user,
                name=name,
                age=age,
                gender=gender,
                blood_type=blood_type,
                health_history=health_history,
                allergies=allergies,
                current_medications=current_medications,
                bad_habits=bad_habits
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        return user


class GenericProfileSerializer(serializers.Serializer):
    """
    Serializer for generic profile updates.
    
    Handles profile updates for all user roles:
    - Patients: Updates Patient model fields (all fields)
    - Staff: Updates User model fields (name, email only)
    
    All fields are optional to support partial updates.
    
    Validates:
    - Email format (RFC 5322 compliant)
    - Age range (0-150)
    
    Requirements: 1.2, 10.1, 10.4
    """
    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    gender = serializers.CharField(max_length=50, required=False)
    age = serializers.IntegerField(min_value=0, max_value=150, required=False)
    blood_type = serializers.CharField(max_length=10, required=False)
    health_history = serializers.CharField(required=False)
    allergies = serializers.CharField(required=False)
    current_medications = serializers.CharField(required=False)
    bad_habits = serializers.CharField(required=False)
