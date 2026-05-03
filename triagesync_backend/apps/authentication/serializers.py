from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    # Public-facing name field (mapped to User.username)
    name = serializers.CharField(max_length=255, required=True)
    # Required demographic field
    age = serializers.IntegerField(min_value=0, max_value=150, required=True)
    # Required for patient registration
    gender = serializers.CharField(max_length=50, required=False, allow_blank=False, allow_null=False)
    blood_type = serializers.CharField(max_length=20, required=False, allow_blank=False, allow_null=False)
    password2 = serializers.CharField(write_only=True, required=True)
    health_history = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allergies = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    current_medications = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bad_habits = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        # include username because it's the model field; API uses `name` instead
        fields = ['username', 'email', 'password', 'password2', 'role', 'name', 'age', 'gender', 'blood_type', 'health_history', 'allergies', 'current_medications', 'bad_habits']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False}
        }

    _BLOOD_TYPE_MAP = {
        "a+": "A+", "a positive": "A+", "a pos": "A+", "a +": "A+",
        "a-": "A-", "a negative": "A-", "a neg": "A-", "a -": "A-",
        "b+": "B+", "b positive": "B+", "b pos": "B+", "b +": "B+",
        "b-": "B-", "b negative": "B-", "b neg": "B-", "b -": "B-",
        "ab+": "AB+", "ab positive": "AB+", "ab pos": "AB+", "ab +": "AB+",
        "ab-": "AB-", "ab negative": "AB-", "ab neg": "AB-", "ab -": "AB-",
        "o+": "O+", "o positive": "O+", "o pos": "O+", "o +": "O+",
        "o-": "O-", "o negative": "O-", "o neg": "O-", "o -": "O-",
    }

    def validate_blood_type(self, value):
        if value is None:
            raise serializers.ValidationError("Invalid blood type")
        normalized = self._BLOOD_TYPE_MAP.get(str(value).strip().lower())
        if not normalized:
            raise serializers.ValidationError("Invalid blood type")
        return normalized

    def validate(self, attrs):
        # Enforce password confirmation when provided by API clients
        password = attrs.get('password')
        password2 = attrs.pop('password2', None)
        if password2 is not None and password != password2:
            raise serializers.ValidationError({'password2': 'Passwords do not match'})

        # For patient role, gender and blood_type are mandatory
        role = attrs.get('role')
        if role == 'patient':
            if not attrs.get('gender'):
                raise serializers.ValidationError({'gender': 'This field is required.'})
            if not attrs.get('blood_type'):
                raise serializers.ValidationError({'blood_type': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        # Map API `name` to User.username
        name = validated_data.pop('name')
        age = validated_data.pop('age')
        validated_data.pop('password2', None)
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

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs


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
    health_history = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allergies = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    current_medications = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bad_habits = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_photo = serializers.FileField(required=False, allow_null=True)
    remove_profile_photo = serializers.BooleanField(required=False)
