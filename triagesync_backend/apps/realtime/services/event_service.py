"""
Event payload builders for all WebSocket event types.
"""

from datetime import datetime, timezone


def _serialize_submission(submission):
    from triagesync_backend.apps.dashboard.serializers import DashboardPatientSerializer

    return DashboardPatientSerializer(submission).data


def _base_event(event_type: str, data: dict) -> dict:
    return {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def build_patient_created_event(submission) -> dict:
    triage_item = _serialize_submission(submission)
    return _base_event(
        "TRIAGE_CREATED",
        {
            "submission_id": submission.id,
            "priority": submission.priority,
            "urgency_score": submission.urgency_score,
            "triage_item": triage_item,
        },
    )


def build_priority_update_event(submission) -> dict:
    triage_item = _serialize_submission(submission)
    return _base_event(
        "PRIORITY_UPDATE",
        {
            "submission_id": submission.id,
            "priority": submission.priority,
            "urgency_score": submission.urgency_score,
            "triage_item": triage_item,
        },
    )


def build_critical_alert_event(submission) -> dict:
    triage_item = _serialize_submission(submission)
    return _base_event(
        "CRITICAL_ALERT",
        {
            "submission_id": submission.id,
            "priority": 1,
            "message": "Critical patient detected!",
            "triage_item": triage_item,
        },
    )


def build_status_changed_event(submission) -> dict:
    triage_item = _serialize_submission(submission)
    return _base_event(
        "TRIAGE_UPDATED",
        {
            "submission_id": submission.id,
            "new_status": submission.status,
            "status": submission.status,
            "triage_item": triage_item,
        },
    )
