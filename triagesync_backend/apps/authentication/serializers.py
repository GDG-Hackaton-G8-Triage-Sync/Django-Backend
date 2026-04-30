from django.contrib.auth import authenticate
from rest_framework import serializers

from triagesync_backend.apps.triage.services.ai_service import (
    normalize_blood_type,
    normalize_gender,
)

from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    # Public-facing name field (mapped to User.username)
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=User.Roles.choices, required=True)
    password2 = serializers.CharField(write_only=True, required=True, trim_whitespace=False)
    # Required demographic field
    age = serializers.IntegerField(min_value=0, max_value=150, required=False)
    # Optional fields (may be provided during registration)
    gender = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    blood_type = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    health_history = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allergies = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    current_medications = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bad_habits = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        # include username because it's the model field; API uses `name` instead
        fields = [
            'username',
            'email',
            'password',
            'password2',
            'role',
            'name',
            'age',
            'gender',
            'blood_type',
            'health_history',
            'allergies',
            'current_medications',
            'bad_habits',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'trim_whitespace': False},
            'username': {'required': False}
        }

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        return value

    def validate_email(self, value):
        email = value.strip().lower()
        queryset = User.objects.filter(email__iexact=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_gender(self, value):
        if value in (None, ""):
            return value
        return normalize_gender(value) or "other"

    def validate_blood_type(self, value):
        if value in (None, ""):
            return value
        normalized = normalize_blood_type(value)
        if not normalized:
            raise serializers.ValidationError("Invalid blood type. Use one of: A+, A-, B+, B-, AB+, AB-, O+, O-.")
        return normalized

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", User.Roles.PATIENT))
        password = attrs.get("password")
        password2 = attrs.get("password2")

        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        if role == User.Roles.PATIENT:
            missing = {}
            for field in ("age", "gender", "blood_type"):
                value = attrs.get(field)
                if value in (None, ""):
                    missing[field] = "This field is required for patient registration."
            if missing:
                raise serializers.ValidationError(missing)

        return attrs

    def create(self, validated_data):
        # Map API `name` to User.username
        name = validated_data.pop('name')
        validated_data.pop('password2')
        age = validated_data.pop('age', None)
        gender = validated_data.pop('gender', None)
        blood_type = validated_data.pop('blood_type', None)
        health_history = validated_data.pop('health_history', None)
        allergies = validated_data.pop('allergies', None)
        current_medications = validated_data.pop('current_medications', None)
        bad_habits = validated_data.pop('bad_habits', None)

        validated_data['username'] = name
        validated_data.setdefault('first_name', name)
        user = User.objects.create_user(**validated_data)

        # Create or update Patient profile for patient role
        if user.role == 'patient':
            from triagesync_backend.apps.patients.models import Patient
            Patient.objects.create(
                user=user,
                name=name,
                age=age or 18,
                gender=gender,
                blood_type=blood_type,
                health_history=health_history,
                allergies=allergies,
                current_medications=current_medications,
                bad_habits=bad_habits
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    identifier = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, data):
        identifier = (
            data.get("identifier")
            or data.get("email")
            or data.get("username")
        )
        password = data.get("password")

        if not identifier:
            raise serializers.ValidationError("Username or email is required")

        auth_username = identifier.strip()

        if "@" in auth_username or data.get("email"):
            user_for_email = User.objects.filter(email__iexact=auth_username).order_by("id").first()
            if user_for_email:
                auth_username = user_for_email.username

        user = authenticate(username=auth_username, password=password)
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
    blood_type = serializers.CharField(max_length=20, required=False)
    health_history = serializers.CharField(required=False)
    allergies = serializers.CharField(required=False)
    current_medications = serializers.CharField(required=False)
    bad_habits = serializers.CharField(required=False)

    def validate_gender(self, value):
        return normalize_gender(value) or "other"

    def validate_blood_type(self, value):
        normalized = normalize_blood_type(value)
        if not normalized:
            raise serializers.ValidationError("Invalid blood type. Use one of: A+, A-, B+, B-, AB+, AB-, O+, O-.")
        return normalized
