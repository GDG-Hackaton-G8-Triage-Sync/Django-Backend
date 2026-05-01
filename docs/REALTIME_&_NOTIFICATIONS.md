# Real-time Events & Notifications

TriageSync uses a dual-channel notification system: **WebSockets** for live updates and **Database Notifications** for persistent history.

## ⚡ WebSocket Connection

**URL**: `ws://<HOST>/ws/triage/events/?token=<JWT_ACCESS_TOKEN>`

### Connection Rules:
- **Staff (Admin/Doctor/Nurse)**: Joined to the global `triage_events` group.
- **Patients**: Joined to their private `user_{id}` group.
- **Authentication**: JWT must be provided as a query parameter.

---

## 📡 Staff Broadcast Events

The following events are pushed to all connected staff members:

### 1. `patient_created`
Broadcast when a new triage submission enters the system.
```json
{
  "event_type": "patient_created",
  "patient_id": 123,
  "priority": 1,
  "urgency_score": 95
}
```

### 2. `priority_update`
Broadcast when a patient's priority is updated (AI or Manual).

### 3. `status_changed`
Broadcast when a patient moves through the workflow (e.g., waiting -> in_progress).

---

## 🔔 Patient Notification System

Patients receive personal notifications for status changes, assignments, or alerts.

### WebSocket Payload (Personal)
```json
{
  "type": "notification",
  "data": {
    "id": 55,
    "notification_type": "triage_status_change",
    "title": "Case Update",
    "message": "A doctor is now reviewing your case.",
    "is_read": false
  }
}
```

### Notification REST API
- `GET /api/v1/notifications/`: List history.
- `GET /api/v1/notifications/unread-count/`: Get count of new messages.
- `PATCH /api/v1/notifications/{id}/read/`: Mark as read.

---

## 🛠️ Implementation Notes

- **Redis**: The production environment **must** have a Redis server configured (`REDIS_URL`) to handle cross-process communication for WebSockets.
- **Offline Delivery**: Notifications are always saved to the DB first. If a user is offline, the WebSocket message is dropped, but they will see the notification in the list when they reconnect.
