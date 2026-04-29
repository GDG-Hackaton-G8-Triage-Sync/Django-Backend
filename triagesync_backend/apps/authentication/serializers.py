from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
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
