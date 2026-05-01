# ⚡ Realtime WebSocket Events

TriageSync utilizes WebSockets to push live triage updates down to the frontend so staff members do not have to manually poll the server.

**Connection URL**: `ws://<HOST>/ws/dashboard/?token=<JWT_ACCESS_TOKEN>`

## 1. Establishing Connections

Flutter clients should initiate a connection to the dashboard channel immediately upon successful login if the user holds a `nurse`, `doctor`, or `admin` role. The JWT access token is required in the query string parameters.

## 2. Supported Event Payloads

### `patient_update`

Emitted when a patient's severity status, assessment, or triage position changes.

```json
{
    "type": "patient_update",
    "data": {
        "patient_id": 1042,
        "status": "critical",
        "updated_at": "2026-04-30T10:00:00Z"
    }
}
```

### `new_triage`

Emitted immediately when a new user completes the AI symptom submission form.

```json
{
    "type": "new_triage",
    "data": {
        "triage_id": 994,
        "severity_score": 8,
        "suggested_action": "Immediate Intervention"
    }
}
```
