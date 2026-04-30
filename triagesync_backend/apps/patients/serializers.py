from rest_framework import serializers

from .models import PatientSubmission, VitalsLog


class TriageSubmissionSerializer(serializers.Serializer):
    symptoms = serializers.CharField(max_length=500)
    language = serializers.CharField(default="en", required=False)
    attachments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )

    def validate_symptoms(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Symptoms cannot be empty.")
        return value


class VitalsLogSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.username", read_only=True)

    class Meta:
        model = VitalsLog
        fields = [
            "id",
            "temperature_c",
            "heart_rate",
            "systolic_bp",
            "diastolic_bp",
            "respiratory_rate",
            "oxygen_saturation",
            "pain_score",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "recorded_by_name", "created_at"]

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one vital measurement is required.")

        oxygen_saturation = attrs.get("oxygen_saturation")
        pain_score = attrs.get("pain_score")

        if oxygen_saturation is not None and not (0 <= oxygen_saturation <= 100):
            raise serializers.ValidationError({"oxygen_saturation": "Must be between 0 and 100."})

        if pain_score is not None and not (0 <= pain_score <= 10):
            raise serializers.ValidationError({"pain_score": "Must be between 0 and 10."})

        return attrs


class PatientSubmissionSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="symptoms", read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_email = serializers.EmailField(source="patient.user.email", read_only=True)
    age = serializers.IntegerField(source="patient.age", read_only=True)
    gender = serializers.CharField(source="patient.gender", read_only=True)
    blood_type = serializers.CharField(source="patient.blood_type", read_only=True)
    health_history = serializers.CharField(source="patient.health_history", read_only=True)
    allergies = serializers.CharField(source="patient.allergies", read_only=True)
    current_medications = serializers.CharField(source="patient.current_medications", read_only=True)
    bad_habits = serializers.CharField(source="patient.bad_habits", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by_user.username", read_only=True)
    reasoning = serializers.CharField(source="reason", read_only=True)
    vitals = VitalsLogSerializer(many=True, read_only=True)
    photo_url = serializers.SerializerMethodField()
    confidence = serializers.FloatField(read_only=True)

    class Meta:
        model = PatientSubmission
        fields = [
            "id",
            "patient",
            "patient_name",
            "patient_email",
            "description",
            "symptoms",
            "priority",
            "urgency_score",
            "condition",
            "category",
            "status",
            "is_critical",
            "photo_name",
            "photo_url",
            "age",
            "gender",
            "blood_type",
            "health_history",
            "allergies",
            "current_medications",
            "bad_habits",
            "explanation",
            "recommended_action",
            "reason",
            "reasoning",
            "confidence",
            "source",
            "vitals",
            "created_at",
            "processed_at",
            "verified_by_user",
            "verified_by_name",
            "verified_at",
        ]
        read_only_fields = fields

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url


class TriageSubmissionHistorySerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.user.email", read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    description = serializers.CharField(source="symptoms", read_only=True)
    reasoning = serializers.CharField(source="reason", read_only=True)
    photo_url = serializers.SerializerMethodField()
    confidence = serializers.FloatField(read_only=True)

    class Meta:
        model = PatientSubmission
        fields = [
            "id",
            "patient_name",
            "patient_email",
            "description",
            "symptoms",
            "priority",
            "urgency_score",
            "condition",
            "category",
            "status",
            "is_critical",
            "photo_name",
            "photo_url",
            "explanation",
            "recommended_action",
            "reason",
            "reasoning",
            "confidence",
            "source",
            "created_at",
            "processed_at",
        ]
        read_only_fields = fields

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url
