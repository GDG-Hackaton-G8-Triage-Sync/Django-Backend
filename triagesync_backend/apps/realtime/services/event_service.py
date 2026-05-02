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
        "TRIAGE_CREATED",
        {
            "submission_id": patient_id,
            "priority": priority,
            "urgency_score": urgency_score,
        },
    )


def build_priority_update_event(patient_id: int, priority: int, urgency_score: int) -> dict:
    """Triggered when AI re-evaluates or updates a patient's priority (M6 calls this)."""
    return _base_event(
        "PRIORITY_UPDATE",
        {
            "submission_id": patient_id,
            "priority": priority,
            "urgency_score": urgency_score,
        },
    )


def build_critical_alert_event(patient_id: int) -> dict:
    """Triggered when priority == 1 (critical case). M6 calls this."""
    return _base_event(
        "CRITICAL_ALERT",
        {
            "submission_id": patient_id,
            "priority": 1,
            "message": "Critical patient detected!",
        },
    )


def build_status_changed_event(patient_id: int, status: str) -> dict:
    """Triggered when staff updates a patient status (waiting/in_progress/completed)."""
    return _base_event(
        "TRIAGE_UPDATED",
        {
            "submission_id": patient_id,
            "new_status": status,
        },
    )


def build_wait_time_update_event(patient_id: int, wait_time_minutes: float, sla_status: str) -> dict:
    """
    Build wait time update event payload.
    
    Args:
        patient_id: PatientSubmission ID
        wait_time_minutes: Current wait time in minutes
        sla_status: One of 'normal', 'warning', 'critical'
    
    Returns:
        Event payload with event_type='WAIT_TIME_UPDATE'
    """
    return _base_event(
        "WAIT_TIME_UPDATE",
        {
            "submission_id": patient_id,
            "wait_time_minutes": wait_time_minutes,
            "sla_status": sla_status,
        },
    )
