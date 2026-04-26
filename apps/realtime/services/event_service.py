def build_event(event_type: str, data: dict) -> dict:
    return {
        "event_type": event_type,
        "data": data,
    }
