from django.contrib import admin
from .models import Patient, PatientSubmission

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "age", "gender", "blood_type")
    search_fields = ("name", "user__username", "user__email")
    list_filter = ("gender", "blood_type")
    readonly_fields = ("user",)
    fieldsets = (
        ("Personal Info", {
            "fields": ("user", "name", "date_of_birth", "age", "gender", "blood_type", "contact_info")
        }),
        ("Clinical History", {
            "fields": ("health_history", "allergies", "current_medications", "bad_habits"),
            "classes": ("collapse",)
        }),
    )

@admin.register(PatientSubmission)
class PatientSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "priority", "urgency_score", "status", "is_critical", "created_at")
    list_filter = ("status", "priority", "is_critical", "created_at", "source")
    search_fields = ("patient__name", "condition", "symptoms")
    readonly_fields = ("created_at", "processed_at", "verified_at")
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Patient & Status", {
            "fields": ("patient", "status", "created_at")
        }),
        ("AI Triage Output", {
            "fields": ("priority", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason", "confidence", "source"),
            "classes": ("extrapretty",)
        }),
        ("Clinical Details", {
            "fields": ("symptoms",)
        }),
        ("Routing Meta", {
            "fields": ("requires_immediate_attention", "specialist_referral_suggested", "critical_keywords"),
            "classes": ("collapse",)
        }),
        ("Workflow & Verification", {
            "fields": ("verified_by_user", "verified_at", "processed_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient", "verified_by_user")
