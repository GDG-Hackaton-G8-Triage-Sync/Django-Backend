from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_triage_event(payload: dict) -> None:
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "triage_events",
        {"type": "triage_event", "payload": payload},
    )
