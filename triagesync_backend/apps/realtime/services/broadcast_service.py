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

