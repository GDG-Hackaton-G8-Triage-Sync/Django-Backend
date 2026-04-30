"""
Broadcast service — sends events to all connected WebSocket clients in the triage group.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from triagesync_backend.apps.patients.models import PatientSubmission

from .event_service import (
    build_critical_alert_event,
    build_patient_created_event,
    build_priority_update_event,
    build_status_changed_event,
)

TRIAGE_GROUP = "triage_events"


def _send(payload: dict) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        TRIAGE_GROUP,
        {"type": "triage_event", "payload": payload},
    )


def _resolve_submission(submission_or_id):
    if isinstance(submission_or_id, PatientSubmission):
        return submission_or_id

    return PatientSubmission.objects.select_related(
        "patient__user",
        "verified_by_user",
    ).prefetch_related("vitals").get(id=submission_or_id)


def broadcast_patient_created(submission_or_id, priority=None, urgency_score=None) -> None:
    submission = _resolve_submission(submission_or_id)
    payload = build_patient_created_event(submission)
    _send(payload)
    if (submission.priority or priority) == 1:
        broadcast_critical_alert(submission)


def broadcast_priority_update(submission_or_id, priority=None, urgency_score=None) -> None:
    submission = _resolve_submission(submission_or_id)
    payload = build_priority_update_event(submission)
    _send(payload)
    if (submission.priority or priority) == 1:
        broadcast_critical_alert(submission)


def broadcast_critical_alert(submission_or_id) -> None:
    submission = _resolve_submission(submission_or_id)
    payload = build_critical_alert_event(submission)
    _send(payload)


def broadcast_status_changed(submission_or_id, status=None) -> None:
    submission = _resolve_submission(submission_or_id)
    payload = build_status_changed_event(submission)
    _send(payload)
