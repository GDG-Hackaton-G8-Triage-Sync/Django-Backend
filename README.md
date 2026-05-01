# TriageSync Backend

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)

TriageSync is an AI-powered medical triage platform that helps healthcare facilities prioritize patient care through intelligent symptom analysis and real-time monitoring.

## 📖 Documentation

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
- `collectstatic` writes files to `STATIC_ROOT` (ensure `STATIC_ROOT` is set via environment / production settings).
- If using a Procfile-style runner, use the same Daphne command but ensure `$PORT` is passed.

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
