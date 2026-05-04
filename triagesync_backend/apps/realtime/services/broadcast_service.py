"""
Broadcast service — sends events to all connected WebSocket clients in the triage group.
Other members (M3, M6) import and call these functions after their logic completes.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .event_service import (
    build_critical_alert_event,
    build_patient_created_event,
    build_priority_update_event,
    build_status_changed_event,
    build_wait_time_update_event,
    build_queue_snapshot_event,
)

TRIAGE_GROUP = "triage_events"


def _send(payload: dict) -> None:
    """Internal helper — pushes a payload to the triage_events channel group."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        TRIAGE_GROUP,
        {"type": "triage_event", "payload": payload},
    )


def broadcast_patient_created(patient_id: int, priority: int, urgency_score: int) -> None:
    """Call this when a new patient submission is saved."""
    payload = build_patient_created_event(patient_id, priority, urgency_score)
    _send(payload)
    if priority == 1:
        broadcast_critical_alert(patient_id)


def broadcast_priority_update(patient_id: int, priority: int, urgency_score: int) -> None:
    """Call this when triage logic updates a patient's priority."""
    payload = build_priority_update_event(patient_id, priority, urgency_score)
    _send(payload)
    if priority == 1:
        broadcast_critical_alert(patient_id)


def broadcast_critical_alert(patient_id: int) -> None:
    """Call this directly for priority-1 critical cases."""
    payload = build_critical_alert_event(patient_id)
    _send(payload)


def broadcast_status_changed(patient_id: int, status: str) -> None:
    """Call this when staff changes a patient's status."""
    payload = build_status_changed_event(patient_id, status)
    _send(payload)


def broadcast_wait_time_update(patient_id: int, wait_time_minutes: float, sla_status: str) -> None:
    """
    Broadcast wait time update for a patient submission.
    
    Args:
        patient_id: PatientSubmission ID
        wait_time_minutes: Current wait time in minutes
        sla_status: One of 'normal', 'warning', 'critical'
    """
    try:
        payload = build_wait_time_update_event(patient_id, wait_time_minutes, sla_status)
        _send(payload)
    except Exception as e:
        # Log error but don't raise - allow system to continue without real-time updates
        import logging
        logger = logging.getLogger("realtime.broadcast")
        logger.error(f"Failed to broadcast wait time update for patient {patient_id}: {e}")


def broadcast_queue_snapshot(submission_id: int) -> None:
    """Broadcast a full queue snapshot for the patient owning the submission.

    Sends the snapshot both to the global triage events group (staff) and
    to the submitting user's private notification group so the patient
    receives an immediate update of their queue state.
    """
    try:
        # Import lazily to avoid circular imports at module load time
        from triagesync_backend.apps.patients.models import PatientSubmission
        from triagesync_backend.apps.patients.views import _build_patient_queue_payload

        submission = PatientSubmission.objects.select_related('patient__user').get(id=submission_id)
        patient = submission.patient

        payload = build_queue_snapshot_event(submission_id, _build_patient_queue_payload(patient))

        channel_layer = get_channel_layer()

        # Send to staff triage group
        async_to_sync(channel_layer.group_send)(
            TRIAGE_GROUP, {"type": "triage_event", "payload": payload}
        )

        # Send private notification to patient user group
        user_group = f"user_{patient.user.id}"
        async_to_sync(channel_layer.group_send)(
            user_group, {"type": "notification_message", "notification": payload}
        )

    except Exception as e:
        import logging
        logger = logging.getLogger("realtime.broadcast")
        logger.warning(f"Failed to broadcast queue snapshot for submission {submission_id}: {e}")

