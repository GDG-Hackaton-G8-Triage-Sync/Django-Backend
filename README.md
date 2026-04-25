# Django-Backend
# TriageSync – Member-7 Data Models

A Django REST API backend for a real-time medical triage system built for the GDG Hackathon. Patients submit symptoms, an AI engine prioritizes them, and medical staff see a live-updating queue via WebSocket.

---

## Tech Stack

- Python / Django 5.1
- Django REST Framework + SimpleJWT
- Django Channels (WebSocket via ASGI)
- PostgreSQL
- Redis (channel layer for production)
- Daphne / Uvicorn (ASGI server)

---

## Project Structure

```
triagesync_backend/
├── apps/
│   ├── authentication/   # JWT auth, user roles (patient/nurse/doctor/admin)
│   ├── core/             # Shared utils, middleware, response helpers
│   ├── patients/         # Patient symptom submission
│   ├── triage/           # AI triage logic + priority engine
│   ├── dashboard/        # Staff/admin dashboard APIs
│   └── realtime/         # WebSocket consumer + broadcast system
└── config/               # Django settings, URLs, ASGI/WSGI
```

---

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Fill in DATABASE_URL, DJANGO_SECRET_KEY, REDIS_URL

# 4. Run migrations
python manage.py migrate

# 5. Start server (ASGI required for WebSocket)
daphne config.asgi:application
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Django secret key |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ⚠️ | Redis URL — falls back to in-memory if not set |
| `DJANGO_DEBUG` | optional | `true` for dev, `false` for prod |
| `DJANGO_ALLOWED_HOSTS` | optional | Comma-separated allowed hosts |
| `CORS_ALLOW_ALL_ORIGINS` | optional | `true` to allow all CORS origins |

---

## API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | Public | Register new user |
| POST | `/api/v1/auth/login/` | Public | Login, get JWT tokens |
| POST | `/api/v1/patients/submit/` | Patient | Submit symptoms |
| GET | `/api/v1/dashboard/patients/` | Staff/Admin | Get patient queue |
| WS | `ws://.../ws/triage/events/` | Staff/Admin | Real-time event stream |

---

## Real-Time WebSocket (Member 8 — Implemented ✅)

### Connection
```
ws://your-domain.com/ws/triage/events/
```

### Event Types Broadcast to Clients

**patient_created** — fires when a new patient submission is triaged
```json
{
  "type": "patient_created",
  "data": { "id": 101, "priority": 2, "urgency_score": 75 },
  "timestamp": "2026-04-24T10:30:00Z"
}
```

**priority_update** — fires when a patient's priority is re-evaluated
```json
{
  "type": "priority_update",
  "data": { "id": 101, "priority": 1, "urgency_score": 92 },
  "timestamp": "2026-04-24T10:31:00Z"
}
```

**critical_alert** — auto-fires when priority == 1 (score >= 80)
```json
{
  "type": "critical_alert",
  "data": { "id": 101, "priority": 1, "message": "Critical patient detected!" },
  "timestamp": "2026-04-24T10:31:00Z"
}
```

**status_changed** — fires when staff updates patient status
```json
{
  "type": "status_changed",
  "data": { "id": 101, "status": "in_progress" },
  "timestamp": "2026-04-24T10:32:00Z"
}
```

### How to Integrate (Flutter)
1. Open WebSocket connection to `ws://your-domain/ws/triage/events/`
2. Listen for incoming JSON messages
3. Parse `type` field to handle each event
4. No need to send anything — this is a server-push only channel

### Testing with Mock Server (no Django needed)
```bash
pip install websockets
python mock_ws_server.py
# Connect Postman/Flutter to ws://localhost:8765
# Receives all event types every 3 seconds
```

---

## Running Tests

```bash
# From triagesync_backend/
pytest apps/realtime/tests.py -v
```

---

## Branches

| Branch | Description |
|---|---|
| `main` | Stable base |
| `dev` | Integration branch — all members merge here |
| `realtimefeater` | Member 8 — WebSocket + broadcast system |
| `member6-triage-logic` | Member 6 — Triage priority engine |
| `feature/AI_service` | Member 5 — AI service layer |
