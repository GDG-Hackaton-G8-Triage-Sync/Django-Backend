import logging
from collections import Counter, defaultdict

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count
from django.utils import timezone

from triagesync_backend.apps.core.validators import validate_status_transition
from triagesync_backend.apps.patients.models import PatientSubmission
from triagesync_backend.apps.realtime.services.broadcast_service import (
    broadcast_priority_update,
    broadcast_status_changed,
)


logger = logging.getLogger("dashboard.service")

SLA_TARGET_MINUTES = {
    1: 5,
    2: 15,
    3: 30,
    4: 60,
    5: 120,
}


def _queue_queryset():
    return PatientSubmission.objects.select_related(
        "patient__user",
        "verified_by_user",
    ).prefetch_related("vitals")


def _wait_minutes(submission, now=None):
    now = now or timezone.now()
    end_time = submission.processed_at or now
    return round(max((end_time - submission.created_at).total_seconds(), 0) / 60, 2)


def _sla_target(priority):
    return SLA_TARGET_MINUTES.get(priority or 3, SLA_TARGET_MINUTES[3])


def get_patient_queue(priority=None, status=None):
    """
    Fetch patients with optional filtering and intelligent ordering.
    """
    queryset = _queue_queryset()

    if priority:
        queryset = queryset.filter(priority=priority)

    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by("priority", "-urgency_score", "created_at")


def get_waiting_analytics(submission):
    """
    Estimate queue position and wait information for a submission.
    """
    if submission.status == PatientSubmission.Status.COMPLETED:
        return {
            "submission_id": submission.id,
            "minutes_waiting": _wait_minutes(submission),
            "queue_position": None,
            "patients_ahead": 0,
            "estimated_wait_minutes": 0,
            "sla_target_minutes": _sla_target(submission.priority),
            "sla_breach_risk": False,
        }

    active_queue = list(
        _queue_queryset()
        .filter(status__in=[PatientSubmission.Status.WAITING, PatientSubmission.Status.IN_PROGRESS])
        .order_by("priority", "-urgency_score", "created_at")
    )
    submission_ids = [item.id for item in active_queue]
    queue_position = submission_ids.index(submission.id) + 1 if submission.id in submission_ids else None
    patients_ahead = max((queue_position or 1) - 1, 0)

    completed_samples = list(
        PatientSubmission.objects.filter(processed_at__isnull=False)
        .order_by("-processed_at")[:50]
    )
    average_turnaround = (
        round(sum(_wait_minutes(item) for item in completed_samples) / len(completed_samples), 2)
        if completed_samples
        else 15.0
    )
    estimated_wait_minutes = round(patients_ahead * average_turnaround, 2)
    minutes_waiting = _wait_minutes(submission)
    sla_target_minutes = _sla_target(submission.priority)

    return {
        "submission_id": submission.id,
        "minutes_waiting": minutes_waiting,
        "queue_position": queue_position,
        "patients_ahead": patients_ahead,
        "estimated_wait_minutes": estimated_wait_minutes,
        "sla_target_minutes": sla_target_minutes,
        "sla_breach_risk": minutes_waiting + estimated_wait_minutes > sla_target_minutes,
    }


def update_patient_status(patient_id, new_status):
    """
    Update workflow status of a patient with validation and broadcast.
    """
    logger.info("Attempting status update for patient %s to %s", patient_id, new_status)

    try:
        patient = _queue_queryset().get(id=patient_id)

        validate_status_transition(patient.status, new_status)

        old_status = patient.status
        patient.status = new_status
        if new_status == PatientSubmission.Status.IN_PROGRESS and not patient.processed_at:
            patient.processed_at = timezone.now()
        elif new_status == PatientSubmission.Status.COMPLETED and not patient.processed_at:
            patient.processed_at = timezone.now()
        patient.save()

        logger.info("Status updated for patient %s: %s -> %s", patient_id, old_status, new_status)
        broadcast_status_changed(patient)
        return patient
    except PatientSubmission.DoesNotExist:
        logger.error("Patient %s not found for status update", patient_id)
        return None
    except ValidationError:
        raise


def get_admin_overview():
    """
    Aggregated system stats.
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
    Analytics payload for the admin dashboard.
    """
    submissions = list(PatientSubmission.objects.all().order_by("created_at"))
    avg_urgency_score = PatientSubmission.objects.aggregate(
        Avg("urgency_score")
    )["urgency_score__avg"]

    common_conditions = list(
        PatientSubmission.objects.values("condition")
        .annotate(count=Count("condition"))
        .order_by("-count")[:5]
    )

    hour_counts = Counter(item.created_at.hour for item in submissions)
    peak_hour = None
    if hour_counts:
        peak_hour_value, peak_hour_count = hour_counts.most_common(1)[0]
        peak_hour = {
            "hour": peak_hour_value,
            "submission_count": peak_hour_count,
        }

    wait_time_buckets = defaultdict(list)
    sla_breach_buckets = defaultdict(int)
    condition_buckets = defaultdict(lambda: {"count": 0, "urgency_total": 0, "critical_count": 0})

    for submission in submissions:
        bucket_key = submission.created_at.date().isoformat()
        wait_minutes = _wait_minutes(submission)
        wait_time_buckets[bucket_key].append(wait_minutes)

        if wait_minutes > _sla_target(submission.priority):
            sla_breach_buckets[bucket_key] += 1

        condition_key = submission.condition or "Unknown"
        condition_bucket = condition_buckets[condition_key]
        condition_bucket["count"] += 1
        condition_bucket["urgency_total"] += submission.urgency_score or 0
        if submission.priority == 1 or submission.is_critical:
            condition_bucket["critical_count"] += 1

    wait_time_trend = [
        {
            "date": bucket_key,
            "average_wait_minutes": round(sum(values) / len(values), 2),
        }
        for bucket_key, values in sorted(wait_time_buckets.items())
    ]

    sla_breach_trend = [
        {
            "date": bucket_key,
            "breaches": breaches,
        }
        for bucket_key, breaches in sorted(sla_breach_buckets.items())
    ]

    condition_summaries = sorted(
        [
            {
                "condition": condition,
                "count": values["count"],
                "average_urgency_score": round(values["urgency_total"] / values["count"], 2) if values["count"] else 0,
                "critical_count": values["critical_count"],
            }
            for condition, values in condition_buckets.items()
        ],
        key=lambda item: (-item["count"], -item["critical_count"], item["condition"]),
    )

    return {
        "avg_urgency_score": avg_urgency_score,
        "common_conditions": common_conditions,
        "peak_hour": peak_hour,
        "wait_time_trend": wait_time_trend,
        "sla_breach_trend": sla_breach_trend,
        "condition_summaries": condition_summaries,
    }


def update_priority(patient, priority):
    """
    Update patient priority with validation and real-time broadcast.
    """
    logger.info("Updating priority for patient %s to %s", patient.id, priority)

    if not isinstance(priority, int) or priority < 1 or priority > 5:
        logger.error("Invalid priority value: %s. Must be 1-5.", priority)
        raise ValueError("Priority must be an integer between 1 and 5")

    old_priority = patient.priority
    patient.priority = priority
    patient.is_critical = priority == 1 or patient.is_critical

    if priority == 1 and (patient.urgency_score or 0) < 80:
        logger.warning(
            "Patient %s set to priority 1 but urgency_score is %s. Adjusting to 85.",
            patient.id,
            patient.urgency_score,
        )
        patient.urgency_score = max(patient.urgency_score or 0, 85)

    patient.save()
    logger.info("Priority updated for patient %s: %s -> %s", patient.id, old_priority, priority)

    broadcast_priority_update(patient)
    return patient


def verify_patient(patient, user):
    if patient.verified_at:
        logger.info("Patient %s already verified, skipping", patient.id)
        return None

    logger.info("Verifying patient %s by user %s", patient.id, user.username)
    patient.verified_by_user = user
    patient.verified_at = timezone.now()
    patient.save()
    logger.info("Patient %s verified successfully by %s", patient.id, user.username)
    return patient
