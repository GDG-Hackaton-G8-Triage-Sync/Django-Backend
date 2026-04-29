"""
Event payload builders for all WebSocket event types.
These are called by M3 (patient submission) and M6 (triage logic) to build
the payload before passing it to broadcast_service.
"""

from datetime import datetime, timezone


def _base_event(event_type: str, data: dict) -> dict:
    return {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_patient_created_event(patient_id: int, priority: int, urgency_score: int) -> dict:
    """Triggered when a new patient submission is created (M3 calls this)."""
    return _base_event(
        "PATIENT_CREATED",
        {
            "id": patient_id,
            "priority": priority,
            "urgency_score": urgency_score,
        },
    )


def build_priority_update_event(patient_id: int, priority: int, urgency_score: int) -> dict:
    """Triggered when AI re-evaluates or updates a patient's priority (M6 calls this)."""
    return _base_event(
        "PRIORITY_UPDATE",
        {
            "id": patient_id,
            "priority": priority,
            "urgency_score": urgency_score,
        },
    )


def build_critical_alert_event(patient_id: int) -> dict:
    """Triggered when priority == 1 (critical case). M6 calls this."""
    return _base_event(
        "CRITICAL_ALERT",
        {
            "id": patient_id,
            "priority": 1,
            "message": "Critical patient detected!",
        },
    )


def build_status_changed_event(patient_id: int, status: str) -> dict:
    """Triggered when staff updates a patient status (waiting/in_progress/completed)."""
    return _base_event(
        "STATUS_CHANGED",
        {
            "id": patient_id,
            "status": status,
        },
    )
