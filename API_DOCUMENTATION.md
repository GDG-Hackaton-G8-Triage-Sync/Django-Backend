# TriageSync API Documentation

Version: 1.2.0
Last Updated: 2026-05-02

This file summarizes the public API surface, deployment notes, ASGI usage, and how the AI (Gemini) responses are consumed by the backend. It is a curated, up-to-date superset of the detailed docs in `/docs`.

---

**Quick Links**
- Main README: [README.md](README.md)
- Full internal docs: `/docs` folder

---

## Deployment & ASGI (concise)

- Project root for deployment: `Django-Backend` (use this as Render root).
- Recommended production server: `daphne` (ASGI). Example start command:

```
python -m daphne -b 0.0.0.0 -p $PORT triagesync_backend.config.asgi:application
```

- Build steps (Render / CI):

```
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

- Important environment variables (summary): `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `RENDER_EXTERNAL_HOSTNAME`, `GEMINI_TIMEOUT_SECONDS`, `GEMINI_MODEL_PRIORITY`.

---

## How AI responses are used (summary)

- The project integrates Google Gemini via an AI wrapper service (`ai_service.py`). Incoming triage submissions call the AI service to obtain structured triage recommendations.
- AI outputs are normalized into the triage result shape with fields such as:
  - `priority` / `priority_level` (1-5)
  - `urgency_score` (0-100)
  - `condition` (string)
  - `category` (string)
  - `is_critical` / `requires_immediate_attention` (bool)
  - `explanation` (array of strings)
  - `recommended_action` (string)
  - `critical_keywords` (array of matched keywords)
  - `specialist_referral_suggested` (bool)
  - `source` ("ai" or "rule")

- Operational notes:
  - Model selection order is driven by `GEMINI_MODEL_PRIORITY` (comma-separated list); the service implements a fallback/circuit-breaker when AI models fail.
  - `GEMINI_TIMEOUT_SECONDS` tunes the request timeout; the service enforces a safe minimum to avoid premature timeouts.
  - When AI is unavailable or fails, the system falls back to deterministic rule-based triage logic and returns a `source: "rule"` result.

---

## Authentication

- JWT auth is used. Include `Authorization: Bearer <token>` header.
- Access/refresh lifetimes are managed by Django settings (see `triagesync_backend/config/settings.py`).

### Endpoints (high-level)

- `POST /api/v1/auth/register/` — Register (patient, staff). Required patient fields: `name`, `email`, `password`, `password2`, `role`, `age`, `gender`, `blood_type`.
- `POST /api/v1/auth/login/` — Login, returns access + refresh tokens.
- `POST /api/v1/auth/refresh/` — Refresh access token.
- `GET|PATCH /api/v1/profile/` — User profile operations.

- `POST /api/v1/triage/` — Submit triage (authenticated patients). The server will run AI analysis and return a structured triage response.
- `POST /api/v1/triage/ai/` — Standalone AI triage analysis (can be unauthenticated; patient fields optional if authenticated).
- `POST /api/v1/triage/pdf-extract/` — Upload PDF for symptom extraction (multipart/form-data).

Triage submissions may include a supporting `photo` upload and optional `photo_name`. Uploaded files are stored under `triage_photos/`, and the backend keeps `recommended_action` with the submission so staff views and notifications can show the AI's suggested next step.

- Staff endpoints under `/api/v1/dashboard/staff/` include queue listing, priority/status updates, and verification endpoints.
- Admin endpoints under `/api/v1/admin/` provide analytics and system overview.

## Pagination

- The API uses a shared `StandardResultsSetPagination` (PageNumber pagination) as the default for list endpoints. Query parameters supported: `page`, `page_size`.
- Default `page_size`: 20. Maximum `page_size`: 100.
- Endpoints that return large lists (staff queue, patient history, notifications) are paginated by default. Individual views may opt out explicitly.

---

## WebSockets / Real-time

- ASGI Channels are used. WebSocket endpoint: `/ws/triage/events/?token=<JWT_ACCESS_TOKEN>`.
- Authentication is supported via either:
  - token query param (`?token=<JWT_ACCESS_TOKEN>`), or
  - `Authorization: Bearer <JWT_ACCESS_TOKEN>` header.
- Only authorized roles should open staff-facing channels.
- Server broadcasts events for `patient_created`, `priority_update`, `critical_alert`, and `status_changed`.

---

## Triage AI Endpoint Behavior

Endpoint: `POST /api/v1/triage/ai/`

Demographic resolution order:

1. Explicit request values (`age`, `gender`, `blood_type`)
2. AI-extracted demographics from `symptoms`
3. Authenticated patient profile fallback

Normalization:

- `age` is normalized to a valid range.
- `gender` is normalized to canonical values.
- `blood_type` is normalized to canonical ABO/Rh format where possible.

Conflict handling:

- If no explicit demographic values are provided and extracted values conflict with profile values, the API can return `409 demographic_conflict` and request clarification.

---

## PDF Extract Endpoint Behavior

Endpoint: `POST /api/v1/triage/pdf-extract/` (multipart/form-data)

- `file` is required and must be a PDF.
- `symptoms` (or `description`) is required: clients must include a short, user-entered description of the patient's current feeling, symptom, or pain along with the PDF. If `symptoms` is omitted the endpoint will return a `400` with `"Missing symptoms prompt."` and instructions to include the prompt.
- When `symptoms` is provided the server validates it for medical relevance before processing the PDF. If the prompt is relevant, the service compares prompt data with extracted PDF demographics and will return `409 demographic_conflict` when there is a disagreement requiring clarification.

Rationale: the service now requires an explicit user complaint to compare against PDF content and to avoid ambiguous file-only submissions. File-only uploads are no longer processed silently.

Demographic fields (`age`, `gender`, `blood_type`) may still be supplied and are used when present.

---

## Blood Type Integration (summary)

- When `blood_type` is provided, AI may include transfusion guidance on severe bleeding.
- The system normalizes various blood type formats and falls back safely when unknown.

---

## Example: Submit triage (patient)

Request:

```json
POST /api/v1/triage/
Authorization: Bearer <access_token>

{
  "description": "Severe chest pain radiating to left arm, shortness of breath"
}
```

Success (201):

```json
{
  "id": 123,
  "description": "Severe chest pain...",
  "priority": 1,
  "recommended_action": "Immediate emergency care",
  "urgency_score": 95,
  "condition": "Acute Cardiac Event",
  "status": "waiting",
  "created_at": "2026-04-29T08:00:00Z",
  "source": "ai"
}
```

---

## Error handling & standard shapes

- Standard error shape used by the API:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable message",
  "details": {}
}
```

Refer to the detailed `docs` folder for per-endpoint examples and full schemas.

---

## Notes for maintainers

- When updating AI integration, prefer updating `triagesync_backend/apps/triage/services/ai_service.py` and `triage/services/prompt_engine.py`.
- To run the project locally for development:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows Powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For production, use the Daphne command above.

---

If you need more detail for a particular endpoint, open the matching file under `/docs` or ask and I will expand this file with request/response schemas for that endpoint.

**Built with ❤️ for better healthcare**
