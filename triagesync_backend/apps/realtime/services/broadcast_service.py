from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _send(group: str, event_type: str, payload: dict) -> None:
    """Internal helper — sends a message to a channel group."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {"type": event_type, "payload": payload},
    )


def broadcast_triage_event(payload: dict) -> None:
    """Generic triage event broadcast."""
    _send("triage_events", "triage_event", payload)


def broadcast_critical_alert(payload: dict) -> None:
    """
    Broadcast a critical_alert event to the triage_events group.
    Called automatically when triage priority == 1.
    Payload should include: urgency_score, condition, message.
    """
    _send("triage_events", "triage_event", {
        "event_type": "critical_alert",
        **payload,
    })


def broadcast_priority_update(payload: dict) -> None:
    """
    Broadcast a priority_update event to the triage_events group.
    Called on every triage evaluation.
    Payload should include: priority, urgency_score, condition.
    """
    _send("triage_events", "triage_event", {
        "event_type": "priority_update",
        **payload,
    })
