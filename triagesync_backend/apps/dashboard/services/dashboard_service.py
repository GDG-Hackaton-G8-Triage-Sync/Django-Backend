from apps.patients.models import PatientSubmission
from django.db.models import Avg, Count
from django.utils import timezone


def get_patient_queue(priority=None, status=None):
    """
    Fetch patients with optional filtering.
    Always sorted by urgency_score DESC (critical first)
    """
    queryset = PatientSubmission.objects.all()

    # Apply filters if provided
    if priority:
        queryset = queryset.filter(priority=priority)

    if status:
        queryset = queryset.filter(status=status)

    # Sort: highest urgency first
    return queryset.order_by("-urgency_score")


def update_patient_status(patient_id, status):
    """
    Update workflow status of a patient
    """
    try:
        patient = PatientSubmission.objects.get(id=patient_id)
        patient.status = status
        patient.save()
        return patient
    except PatientSubmission.DoesNotExist:
        return None


def get_admin_overview():
    """
    Aggregated system stats
    """
    return {
        "total_patients": PatientSubmission.objects.count(),
        "waiting": PatientSubmission.objects.filter(status="waiting").count(),
        "in_progress": PatientSubmission.objects.filter(status="in_progress").count(),
        "completed": PatientSubmission.objects.filter(status="completed").count(),
        "critical_cases": PatientSubmission.objects.filter(priority=1).count(),
    }


def get_admin_analytics():
    """
    Optional analytics data
    """
    return {
        "avg_urgency_score": PatientSubmission.objects.aggregate(
            Avg("urgency_score")
        )["urgency_score__avg"],
        "common_conditions": list(
            PatientSubmission.objects.values("condition")
            .annotate(count=Count("condition"))
            .order_by("-count")[:3]
        ),
    }

def update_priority(patient, priority):
    patient.priority = priority
    patient.save()
    return patient


def verify_patient(patient, user):
    if patient.verified_at:
        return None

    patient.verified_by = user.username
    patient.verified_at = timezone.now()
    patient.save()
    return patient