# TriageSync — Integration Plan

A member-by-member integration map. Each member section has **two parts**:

- **What I Provide** — the outputs / functions / data shapes that other members consume.
- **What I Need** — the inputs / functions / guarantees this member depends on others for.

The same handshake appears in two members' sections, written from each side. Reading either side gives a complete view of that integration point.

---

## How to read this document

Every integration point in the system is a contract between two members. A contract has:

- A **producer** (the member who exposes a function, emits an event, or writes a row).
- A **consumer** (the member who calls the function, listens for the event, or reads the row).

If a contract changes, **both sides update simultaneously**. The producer cannot rename a field without the consumer knowing. The consumer cannot start expecting a new field without the producer agreeing to emit it.

Use this document to:
1. Find which other members you must coordinate with before changing your code.
2. Find every input you can rely on and every output you must produce.
3. Resolve disputes — if your code breaks, walk the contract and confirm both sides are honoring it.

---

## Locked system flow

```
                 (auth)            (auth)
   Patient ──► M2 ──► M3 ─────────► M6 ──► M5 (AI)
                       │             │      │
                       │             ▼      ▼
                       │            M7 ◄── normalized dict
                       │            (DB)
                       ▼             │
                      M8 ──── case.triaged event
                       │             │
                       └─────────────┴──────► Staff browser
                                              │
                                              ▼
                                       M4 (REST refresh)
                                              │
                                              ▼
                                            M7 (read)
```

Cross-cutting (touch every step): **M1** (response/exception envelope) and **M2** (permissions on every endpoint).

---

## Member 1 — Core Backend & Shared Infrastructure

**Module:** `apps/core/`
**Status:** Partial — `constants.py`, `exceptions.py`, `response.py`, `middleware.py`, `payload_sanitizer.py` exist.

### What I Provide

- **To everyone — `apps.core.response.ApiResponse(data, status, ...)`**
  Standard success/error envelope wrapper. Every view should return through this so the frontend sees a consistent shape.
- **To everyone — global exception handler**
  Maps unhandled exceptions to JSON envelopes with HTTP status codes. Configured in `settings.REST_FRAMEWORK["EXCEPTION_HANDLER"]`.
- **To M3, M5 — `PayloadSanitizerMiddleware`** (registered in `settings.MIDDLEWARE`)
  Strips PII from inbound JSON on `/api/v1/triage/*`. Whitelist: `age`, `gender`, `symptoms`. Attaches `request._triage_warning` if age/gender missing.
- **To everyone — shared validators / utilities**
  Length checks, required-field validators, request-ID generator (`apps.core.utils.generate_request_id`).

### What I Need

- **From everyone** — agree to wrap their `Response(...)` calls in `ApiResponse(...)` rather than returning raw DRF responses.
- **From M2** — confirmation that exception messages don't leak auth details (M1's handler must mask sensitive fields).
- **From M8** — agreement on which exception classes to broadcast as system events (e.g., circuit breaker opens).

---

## Member 2 — Authentication & Security

**Module:** `apps/authentication/`
**Status:** Models scaffolded — `User` with role choices (`patient`, `nurse`, `doctor`, `admin`).

### What I Provide

- **To M3, M4, M5 (views), M8 (WebSocket)** — `IsAuthenticated` + role-based permission classes.
  Concrete classes: `IsPatient`, `IsStaff` (nurse/doctor), `IsAdmin`.
- **To everyone** — `request.user` populated on every authenticated request (a `User` model instance with `.role`).
- **To M3** — JWT token issuance: `POST /api/v1/auth/login/`, `POST /api/v1/auth/refresh/`.
- **To M8** — WebSocket auth middleware (validates JWT on connect, rejects anonymous sockets).

### What I Need

- **From M7** — the `User` model's role field and any FK relationships (e.g., `User → cases`).
- **From M3, M4, M5** — declaration of which permission class each endpoint uses. Default is `IsAuthenticated` but must be tightened per role.
- **From M8** — the WebSocket connection scope so the auth middleware can attach the user to the channel.

---

## Member 3 — Patient API (Input Layer)

**Module:** `apps/patients/`
**Status:** Mock — `PatientSubmission` model + mock status responses.

### What I Provide

- **To patients (HTTP clients)** — `POST /api/v1/triage/` accepting `{symptoms, age?, gender?}`.
  Validates input (≤ 500 chars), creates a session, and starts the pipeline.
- **To M6** — calls `evaluate_triage(symptoms, age, gender)` and persists nothing itself; M6 owns the write.
- **To M8** — emits `case.submitted` event via `broadcast_service.emit("case.submitted", payload)` immediately after a valid submission.
- **To M7** — passes the authenticated `request.user` into the M6 call so the patient FK can be set on the resulting `TriageResult` row.
- **To M4** — optional patient-history endpoint: `GET /api/v1/patients/me/history/` returning the caller's past triage results.

### What I Need

- **From M2** — `IsPatient` permission class on `POST /api/v1/triage/`. Without it, anonymous traffic reaches Gemini and burns quota.
- **From M1** — `ApiResponse` envelope so the frontend gets a uniform `{data, error, request_id}` shape.
- **From M1 (`PayloadSanitizerMiddleware`)** — already strips disallowed keys before the view runs; M3 must not re-add them.
- **From M5 (indirect, via M6)** — guarantee that `evaluate_triage` always returns a dict, never raises. M3's view must not have try/except around the AI call.
- **From M6** — the exact return shape of `evaluate_triage` so M3's serializer can validate it before responding.
- **From M7** — the `User` model and the migration that lets M6 store a `patient` FK.
- **From M8** — the `broadcast_service.emit` signature and the agreed event name `case.submitted` with its payload schema.

---

## Member 4 — Dashboard API (Output Layer)

**Module:** `apps/dashboard/`
**Status:** Mock — hardcoded counts and status updates.

### What I Provide

- **To staff browser** — `GET /api/v1/dashboard/staff/queue/` returning a paginated list of active triage cases ordered by `(is_critical DESC, priority_level ASC, created_at ASC)`.
- **To staff browser** — `GET /api/v1/dashboard/staff/patient/{session_id}/` returning a single case with full triage detail.
- **To staff browser** — `POST /api/v1/dashboard/staff/patient/{session_id}/override/` for manual priority/status overrides (delegates to M6).
- **To admin browser** — `GET /api/v1/dashboard/admin/overview/` with aggregate stats (counts by priority, average urgency, daily volume).
- **To M8** — payload schema for live updates. M4 defines the JSON shape that `case.triaged` / `case.status_changed` events should carry, so the frontend can reuse the same renderer for REST and WebSocket data.

### What I Need

- **From M2** — `IsStaff` permission on staff endpoints, `IsAdmin` on admin endpoints.
- **From M7** — `TriageResult` model with the full set of fields (status, assigned_to, resolved_at) and a query manager method like `TriageResult.objects.active_queue()`.
- **From M6** — the override entry point: `triage_service.override_case(session_id, actor, **changes)` which validates the transition and emits the event.
- **From M8** — the event names and payload contract so M4's WebSocket-side renderer matches its REST-side renderer.
- **From M1** — `ApiResponse` envelope.

---

## Member 5 — AI Service Layer  *(this member)*

**Module:** `apps/triage/services/ai_service.py`, `apps/triage/services/prompt_engine.py`
**Status:** Production-ready. Multi-model cascade, thread-safe circuit breaker, JSON-mode parsing, retry-skip on deterministic errors, prompt-injection hardening.

### What I Provide

- **To M6 — `get_triage_recommendation(symptoms, age=None, gender=None, model_name=None) -> dict`**
  Always returns a dict, never raises. Two shapes:

  **Success:**
  ```python
  {
    "priority_level": int,        # 1..5, clamped
    "urgency_score":  int,        # 0..100, clamped
    "condition":      str,
    "category":       str,        # one of: Cardiac, Respiratory, Trauma, Neurological, General
    "is_critical":    bool,
    "explanation":    list[str],
    "recommended_action": str,
    "reason":         str,
  }
  ```

  **Failure:**
  ```python
  {
    "error": "AI unavailable, staff review required",
    "user_description": str,
    "details":     list[str],
    "error_types": list[str],     # e.g. ["quota", "timeout", "circuit_open"]
  }
  ```

- **To M3 (indirectly) — `POST /api/v1/triage/pdf-extract/`**
  Accepts a PDF upload, returns extracted text for re-submission as `symptoms`.
- **To M6 — `normalize_ai_response(data) -> dict`**
  Schema hygiene only (clamps, enum coercion, type coercion). **Does not** apply priority↔critical coupling — that is M6's policy layer.
- **To M1 / M8** — circuit-breaker state and structured error envelopes that can be surfaced as system events.

### What I Need

- **From M3** — calls routed through M6, not directly to me. M3 must not call `get_triage_recommendation` itself.
- **From M6** — re-application of the priority↔critical coupling rules I deliberately removed (L1 ⇒ critical, critical ⇒ priority ≤ 2, plus any future hospital-specific rules).
- **From M6** — fallback orchestration. When my dict has `"error"`, M6 decides whether to substitute a rule-based answer or surface the failure.
- **From M1** — `PayloadSanitizerMiddleware` registered upstream so my prompts only ever see whitelisted fields.
- **From M2** — permission gate on `/api/v1/triage/ai/` and `/pdf-extract/`. Confirm whether these are patient-callable or staff-only.
- **From config (M1 / DevOps)** — `GEMINI_API_KEY` and `GEMINI_MODEL_PRIORITY` env vars present at boot.

---

## Member 6 — Triage Logic & Business Rules

**Module:** `apps/triage/services/triage_service.py`, `apps/triage/services/validation_service.py`
**Status:** Scaffold only — 26 lines wrapping M5's output, no policy applied yet.

### What I Provide

- **To M3, M4 — `evaluate_triage(symptoms, age=None, gender=None, *, patient=None) -> dict`**
  Single entry point for the full triage pipeline. Internally:
  1. Calls M5's `get_triage_recommendation(...)`.
  2. On success: applies priority↔critical coupling and any hospital policy rules.
  3. On error: applies fallback substitution (rule-based answer) or re-raises as an envelope.
  4. Persists via M7 (`TriageResult.objects.create(...)`).
  5. Emits the appropriate M8 event (`case.triaged` or `case.escalated`).
  Returns the persisted dict (with `session_id`, `status`, `created_at`).
- **To M4 — `override_case(session_id, actor, **changes) -> dict`**
  Validates a status / priority transition, writes the change, emits `case.status_changed`.
- **To M4 / M7 — status state machine.**
  Defines the legal transitions (e.g., `queued → in_review → resolved`, `queued → escalated`) and the `Status` enum stored in `apps/core/constants.py`.
- **To M8** — emits `case.triaged`, `case.escalated`, `case.status_changed` events with payloads agreed with M4.
- **To M5** — nothing direct; M6 is a pure consumer of M5's output.

### What I Need

- **From M5** — `get_triage_recommendation(...)` always returning a dict with the documented success or error shape.
- **From M5** — `normalize_ai_response(...)` already applied (clamps + enum coercion + bool coercion done before I see the dict).
- **From M7** — extended `TriageResult` model with `patient` FK, `status`, `assigned_to`, `resolved_at`, `urgency_score`, `category`, `is_critical`, `recommended_action`, `reason`, and `explanation` as `JSONField`.
- **From M7** — query helpers: `TriageResult.objects.active_queue()`, `TriageResult.objects.for_patient(user)`.
- **From M3** — calls routed exclusively through `evaluate_triage(...)`. M3 must not call M5 directly.
- **From M4** — agreement on the override payload schema (`{priority_level?, status?, assigned_to?, reason}`).
- **From M8** — `broadcast_service.emit(event_type, payload)` available and idempotent.
- **From M1** — `ApiResponse` envelope and a typed exception class for "transition not allowed" errors.
- **From M2** — `actor` (the staff user) is guaranteed authenticated and authorized before reaching `override_case`.

---

## Member 7 — Data Layer (Models & Queries)

**Module:** `apps/patients/models.py`, `apps/triage/models.py`, `apps/authentication/models.py`
**Status:** Minimal — `TriageResult` has only `priority`, `explanation`, `created_at`; no status field, no patient FK.

### What I Provide

- **To M2 — `User` model** with `role` (`patient`, `nurse`, `doctor`, `admin`) and any related fields M2 needs for permission checks.
- **To M3 — `PatientSubmission` model** (or equivalent) for storing raw inbound submissions.
- **To M6 — extended `TriageResult` model** with the full schema:
  ```python
  class TriageResult(models.Model):
      patient            = ForeignKey(User, on_delete=CASCADE, related_name="triage_results")
      session_id         = UUIDField(default=uuid4, unique=True)
      symptoms           = TextField()
      priority_level     = IntegerField()
      urgency_score      = IntegerField()
      category           = CharField(max_length=32, choices=CATEGORY_CHOICES)
      is_critical        = BooleanField(default=False)
      explanation        = JSONField(default=list)
      recommended_action = TextField()
      reason             = TextField()
      status             = CharField(max_length=24, choices=STATUS_CHOICES, default="queued")
      assigned_to        = ForeignKey(User, null=True, blank=True, related_name="assigned_cases")
      created_at         = DateTimeField(auto_now_add=True)
      updated_at         = DateTimeField(auto_now=True)
      resolved_at        = DateTimeField(null=True, blank=True)
  ```
- **To M4 — query managers / methods**:
  `TriageResult.objects.active_queue()`, `TriageResult.objects.for_patient(user)`, `TriageResult.objects.aggregate_overview()`.
- **To everyone** — migrations applied cleanly on the Neon Postgres database.
- **To admin (M4)** — admin APIs: user management, patient management.

### What I Need

- **From M6** — final field list and choice values for `status`, `category`, and `priority_level` so the migration is correct first time.
- **From M2** — the `User` model's role choices and any custom fields (e.g., `is_active`, `staff_id`).
- **From M4** — the exact aggregations needed (counts, averages, time windows) so I can index appropriately.
- **From M1** — exception class hierarchy so model-level validation errors (e.g., `IntegrityError`) map to the standard envelope.
- **From DevOps / M1** — Neon Postgres connection string + migration runbook.

---

## Member 8 — Real-Time System & Backend Testing

**Module:** `apps/realtime/consumers.py`, `apps/realtime/routing.py`, `apps/realtime/services/broadcast_service.py`
**Status:** Stub — needs Channels + Redis configuration.

### What I Provide

- **To M3, M6 — `broadcast_service.emit(event_type: str, payload: dict, *, group: str = "staff") -> None`**
  Single entry point for all real-time fan-out. Idempotent and non-blocking.
- **To staff browsers** — WebSocket endpoint `ws://.../ws/triage/staff/` that streams events to authenticated staff.
- **To admin browsers** — WebSocket endpoint `ws://.../ws/triage/admin/` for admin-level events.
- **To everyone — agreed event catalog**:

  | Event              | Emitter | Payload                                              | Group          |
  |--------------------|---------|------------------------------------------------------|----------------|
  | `case.submitted`   | M3      | `{session_id, patient_id, created_at}`               | `staff`        |
  | `case.triaged`     | M6      | full `TriageResult` dict                             | `staff`        |
  | `case.escalated`   | M6      | `{session_id, priority_level, reason}`               | `staff,admin`  |
  | `case.status_changed` | M6   | `{session_id, from, to, actor_id, changed_at}`       | `staff`        |

- **To M1, M2, M3, M4, M5, M6, M7** — backend test suite (Postman collection + pytest integration tests + performance/load scripts).

### What I Need

- **From M2** — WebSocket auth middleware that validates the JWT on connect and attaches `scope["user"]`.
- **From M3** — calls to `emit("case.submitted", ...)` after every successful submission.
- **From M6** — calls to `emit("case.triaged" / "case.escalated" / "case.status_changed", ...)` at the agreed lifecycle points.
- **From M4** — payload schema declaration so the WebSocket-side renderer matches the REST-side renderer.
- **From M7** — agreement that no event will reference a row that hasn't been committed yet (M6 must persist before emitting).
- **From M1** — exception class for "broadcast failed" so failures don't crash the request path.
- **From DevOps / M1** — Redis connection string for the channel layer.

---


## Reciprocal handshake matrix

Every row is one contract, written from both sides. If you change either side, both rows of the corresponding section must be updated.

| Contract | Producer says "I provide…" | Consumer says "I need…" |
|---|---|---|
| Authentication | M2: JWT issuance + permission classes | M3, M4, M5: permission class on every endpoint |
| WebSocket auth | M2: WS auth middleware | M8: validated `scope["user"]` on connect |
| Standard response envelope | M1: `ApiResponse(...)` wrapper | M3, M4, M5, M6: wrap every view return |
| Payload sanitization | M1: `PayloadSanitizerMiddleware` | M5: prompts only see whitelisted fields |
| AI dict | M5: `get_triage_recommendation(...)` | M6: dict (success or error envelope) |
| Triage policy entry point | M6: `evaluate_triage(...)` | M3: single call, no direct M5 access |
| Override entry point | M6: `override_case(...)` | M4: validated transitions + event emit |
| `TriageResult` schema | M7: extended model + managers | M6: persistence target with all fields |
| Query helpers | M7: `active_queue()`, `for_patient()`, `aggregate_overview()` | M4: dashboard reads |
| Submission event | M3: `emit("case.submitted", ...)` | M8: payload to fan out |
| Triage event | M6: `emit("case.triaged" / "case.escalated", ...)` | M8: payload to fan out |
| Status-change event | M6: `emit("case.status_changed", ...)` | M4, M8: live dashboard refresh |
| Event catalog | M8: agreed event names + schemas | M3, M4, M6: emit / consume the same shapes |

---

## Integration phases (recommended order)

Build in dependency order. Each phase ends with a contract test that two members run together.

### Phase A — Foundation (parallel, no dependencies)

| Task | Owner | Unblocks |
|---|---|---|
| JWT + role permissions | M2 | M3, M4 endpoints |
| Standard `ApiResponse` + exception handler | M1 | All views |
| Real `TriageResult` schema with FKs and status | M7 | M6, M4 |
| **AI service + prompt engine + tests** | **M5 (done)** | M6 |

**Exit criterion:** M7's migrations run cleanly on Neon; M2's `IsAuthenticated` rejects anonymous requests; M5's tests pass; M1's response wrapper is used by at least one view.

### Phase B — Core triage path (sequential)

1. **M6** implements `evaluate_triage()` — consumes M5's dict, applies policy, calls M7 to persist.
2. **M3** rewires `PatientTriageView.post()` to call `evaluate_triage()` instead of returning mock data.
3. **M3** + **M6** emit their respective events through M8's `broadcast_service.emit()`.
4. **M8** wires `consumers.py` to subscribe groups by role (`staff`, `admin`).
5. **M4** swaps mock counts for real ORM queries on `TriageResult`.

**Exit criterion:** A patient `POST /api/v1/triage/` produces a real DB row, the staff dashboard endpoint returns it, and a connected WebSocket client receives a `case.triaged` event within 1 s.

### Phase C — Hardening

| Task | Owner |
|---|---|
| Status transition endpoint with validated transitions | M6 + M4 |
| Critical-alert escalation event wired to WebSocket | M6 + M8 |
| Performance / integration test suite | M8 |
| Audit log on every transition | M6 + M7 |
| Admin overview aggregations (real queries) | M4 + M7 |

---

## High-risk seams (will break silently if ignored)

| Seam | Members involved | Failure mode if uncoordinated |
|---|---|---|
| AI dict shape | M5 ↔ M6 | M6's serializer fails when M5 changes a key name |
| `TriageResult` schema | M6 ↔ M7 | M6 writes fields M7 didn't migrate → runtime errors |
| Event payload shape | M3 / M6 ↔ M8 ↔ M4 | Frontend receives unexpected JSON, dashboard breaks silently |
| Permission classes | M2 ↔ everyone | An endpoint forgets the class → unauth POSTs reach M5, burn Gemini quota |

Lock each of these in writing (this document or a short `contracts.py`) **before** parallel work starts.

---

## One-paragraph summary

> A patient POSTs symptoms to **M3**, which (after **M2** authenticates) calls **M6**'s `evaluate_triage()`. M6 calls **M5**'s `get_triage_recommendation()` and gets back either a clean dict or an error envelope. M6 applies priority-mapping policy, decides on fallback if needed, and persists the result via **M7**'s ORM, transitioning status to `queued` (or `escalated` if critical). M6 emits `case.triaged` through **M8**'s broadcast service. M8 fans the event to subscribed staff WebSocket connections. **M4**'s dashboard endpoint queries M7 for the same data on REST refresh. **M1** wraps every response in the standard envelope. Every step except the AI call itself is gated on **M2**'s permission class.
