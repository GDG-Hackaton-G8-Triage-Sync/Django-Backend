from django.contrib import admin

from .models import Patient, PatientSubmission, VitalsLog


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "age", "gender", "blood_type")
    search_fields = ("name", "user__username", "user__email", "blood_type")
    list_filter = ("gender", "blood_type")


@admin.register(PatientSubmission)
class PatientSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "priority",
        "urgency_score",
        "condition",
        "status",
        "is_critical",
        "created_at",
    )
    search_fields = ("patient__name", "patient__user__email", "condition", "symptoms")
    list_filter = ("status", "priority", "is_critical", "category")
    autocomplete_fields = ("patient", "verified_by_user")
    readonly_fields = ("created_at", "processed_at", "verified_at")


@admin.register(VitalsLog)
class VitalsLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "submission",
        "recorded_by",
        "temperature_c",
        "heart_rate",
        "oxygen_saturation",
        "created_at",
    )
    search_fields = ("submission__patient__name", "submission__patient__user__email", "recorded_by__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("submission", "recorded_by")
    readonly_fields = ("created_at",)
