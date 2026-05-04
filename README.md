# TriageSync Backend

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)
![Mode](https://img.shields.io/badge/engine-ASGI/Daphne-orange.svg)

TriageSync is an AI-powered medical triage platform that helps healthcare facilities prioritize patient care through intelligent symptom analysis and real-time monitoring.

## 🚀 Latest Updates (May 2026)

- **⚡ Asynchronous Support**: The server now runs on **ASGI (Daphne)**, supporting concurrent WebSocket connections and non-blocking real-time events.
- **🧠 Enriched AI Reasoning**: Triage results now include **Confidence Scores (0-100%)**, clinical rationale, and symptom extraction.
- **👨‍⚕️ Advanced Staff Tools**: Improved permissions allowing Admins and Staff to view full Clinical Profiles and manage staff assignments.
- **📊 Command Center Analytics**: Real-time hourly trends for Wait Times and SLA Breach Velocity.
- **🧾 Patient Queue Tracking**: New patient queue endpoints with real-time snapshot updates over WebSockets.

## 📖 Documentation Index

For detailed information, please refer to the specialized guides in the `/docs` directory:

- [**Authentication & Roles**](./docs/AUTH_&_USER_ROLES.md) - JWT, RBAC, and Security.
- [**API Reference**](./docs/API_REFERENCE.md) - All REST endpoints and examples.
 - [**Real-time & Notifications**](./docs/REALTIME_&_NOTIFICATIONS.md) - WebSockets and alerts.
 - [**Flutter Integration**](./docs/INTEGRATION_GUIDE.md) - Mobile-specific implementation guide.
 - [**AI System**](./docs/AI_SYSTEM.md) - Gemini AI logic and priority levels.

## 🛠️ Core Features

- **AI-Powered Triage**: Real-time symptom analysis using Google Gemini.
- **Dynamic Queue**: Automated patient sorting by severity and urgency.
- **Real-time Updates**: Instant WebSocket notifications for staff and patients.
- **Clinical Notes**: Secure staff-only notes and vitals logging.
- **Admin Dashboard**: System-wide analytics and user management.

## AI Triage Input Resolution

For `POST /api/v1/triage/ai/`, demographic inputs are resolved with clear priority:

1. Explicit request values (`age`, `gender`, `blood_type`)
2. Demographics extracted from symptoms text
3. Authenticated patient profile fallback

Resolved values are normalized before the AI call (age bounds, canonical gender, canonical blood type).
If conflicting demographics are detected between extracted and profile values (and no explicit values were sent), the endpoint returns a conflict response and asks the client to clarify.
Note: the AI triage endpoint accepts an explicit `symptoms`/`description` field; authenticated patient profile fields are merged as fallback only when explicit values are not provided.

## Triage Submission Response

`POST /api/v1/triage/` stores the AI output on the patient submission record and now returns the `recommended_action` alongside the priority, urgency score, and condition.
That field is also propagated into notification metadata so staff-facing alerts can show the same recommended next step the AI generated.

## Photo Upload Usage

The AI triage endpoint accepts an optional `image` upload, stores it under `triage_attachments/`, and returns an `image_url` for staff viewing. The image is not sent to the AI model.

Profile photos are handled via the patient profile API (`/api/v1/patients/profile/`), which accepts an optional `profile_photo` file and exposes `profile_photo_name` for display.

For historical and audit purposes, legacy fields `PatientSubmission.photo` and `PatientSubmission.photo_name` remain in the database and may contain prior uploads, but triage flows will not populate these fields going forward.

## PDF Triage Behavior

`POST /api/v1/triage/pdf-extract/` accepts multipart PDF uploads and now requires a user-entered symptoms/description prompt alongside the file. The endpoint behavior is:

- `file` (PDF) is required and must contain selectable text when applicable.
- `symptoms` (or `description`) is required: the server will validate the provided text for medical relevance before processing the PDF.
- If the request is file-only (no `symptoms` provided), the endpoint returns a `400` response with `"Missing symptoms prompt."` and an instruction to provide a brief description of the patient's current feeling, symptom, or pain.

Rationale: a typed symptoms prompt is required so the AI can compare user-entered complaints against the PDF contents and avoid ambiguous file-only submissions. Conflict detection between the prompt and PDF demographics still applies, but only when a prompt is present.

## WebSocket Authentication

WebSocket connections support both methods:

- Query token: `/ws/triage/events/?token=<JWT_ACCESS_TOKEN>`
- Authorization header: `Authorization: Bearer <JWT_ACCESS_TOKEN>`

Use either method depending on client platform constraints.

Note: WebSocket middleware accepts both query token and Authorization header for backwards compatibility with older clients.

## Real-time Queue Snapshots

Patient queue state is broadcast in real time via WebSockets using the `queue_snapshot` event. The payload mirrors the response shape of `GET /api/v1/patients/queue/`, so clients can replace their local queue state directly.

## 🚀 Deployment

The project is configured for seamless deployment on **Render** using the provided `render.yaml` and `build.sh`.

### Environment Variables Required:
- `SECRET_KEY`: Django secret key.
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Required for WebSockets (Production).
- `GEMINI_API_KEY`: Google AI Studio API key.
 - `RENDER_EXTERNAL_HOSTNAME`: (optional) Render hostname used to populate `ALLOWED_HOSTS` when deployed on Render.
 - `GEMINI_TIMEOUT_SECONDS`: (optional) Timeout for AI calls (default set in settings).
 - `GEMINI_MODEL_PRIORITY`: (optional) Comma-separated model list the AI service will try in order.

### Render build & start (recommended)

Set the service root to the repository subfolder: `Django-Backend`.

Build command (Render):

```
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Start command (Render):

```
python -m daphne -b 0.0.0.0 -p $PORT triagesync_backend.config.asgi:application
```

Notes:
- The app expects an ASGI server in production (Daphne is recommended and already added to `requirements.txt`).
- Daphne is a server/runtime dependency, not a Django app, so it should not be added to `INSTALLED_APPS`.
- `collectstatic` writes files to `STATIC_ROOT` (ensure `STATIC_ROOT` is set via environment / production settings).
- If using a Procfile-style runner, use the same Daphne command but ensure `$PORT` is passed.

### Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://django-backend-subb.onrender.com/`

## 🧪 Testing

The backend includes a comprehensive test suite (Unit, Integration, and AI service tests).

```bash
# Run all tests
pytest

# Run specific feature tests
pytest triagesync_backend/apps/triage/tests/
```

---
Built with ❤️ by the TriageSync Team.
