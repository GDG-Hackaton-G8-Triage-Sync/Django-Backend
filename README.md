# Member 5 — AI Infrastructure & Gemini Integration

Production-grade AI layer for the TriageSync medical triage platform. This
document describes **only** what Member 5 owns: the AI pipeline that turns a
patient symptom description (or PDF extract) into a structured triage JSON
object, plus the operational safeguards around the Gemini API call.

> **Scope boundary.** M5 covers the "how" of AI (API calls, retries, parsing,
> prompt safety, schema hygiene). The "what" of triage — priority/criticality
> coupling rules, urgency scoring policy, and rule-based fallback substitution —
> is Member 6's responsibility and is intentionally **not** implemented here.

---

## 1. What Is Implemented

### 1.1 Gemini API client (`services/ai_service.py`)
- **Multi-model priority list** with automatic fallback between `gemini-2.5-flash`
  and `gemini-1.5-flash` (configurable allow-list).
- **Cached `list_models()` discovery.** Thread-safe, TTL-based cache (default
  600 s). Intersects the configured allow-list with models actually enabled
  for the API key. Cache is refreshed lazily and can be invalidated via
  `invalidate_model_list_cache()`.
- **Retry with exponential backoff.** Each model is tried `GEMINI_MAX_RETRIES`
  times with `2^(attempt-1)` second sleeps between attempts.
- **Per-call timeout.** Every `generate_content` call runs in a
  `ThreadPoolExecutor` with an `GEMINI_TIMEOUT_SECONDS` wall-clock budget so a
  single hung model cannot stall the endpoint.
- **Circuit breaker.** After `GEMINI_CIRCUIT_BREAKER_THRESHOLD` consecutive
  end-to-end failures, all further calls are short-circuited for
  `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`. Any success resets the counter.
  Exposed as `reset_circuit_breaker()` for tests/ops.
- **JSON mode.** Models are constructed with
  `generation_config={"response_mime_type": "application/json"}` so output is
  guaranteed to be a single valid JSON object with no markdown fences.
- **Error classification.** Single source of truth mapping raw exception text
  to `quota` / `not_found` / `other` categories (`_classify_model_error`).
- **Structured error envelope.** On total failure, returns a JSON string
  containing `error`, `user_description`, `details` (per-attempt failure list),
  and `error_types` (deduplicated category list).

### 1.2 Prompt engine (`services/prompt_engine.py`)
- `build_triage_prompt(symptoms, age, gender)` — user-symptom triage prompt.
- `build_pdf_triage_prompt(text, age, gender)` — PDF-extract triage prompt.
- **Prompt-injection hardening.** User/PDF content is wrapped in
  `<user_symptoms>…</user_symptoms>` / `<pdf_text>…</pdf_text>` blocks with
  explicit instructions to treat the content strictly as data. Any
  pre-existing delimiter tokens in the input are stripped before interpolation
  so a patient cannot break out of the data block.
- **Demographics handling.** Missing age/gender render as `unknown`; provided
  values are echoed in the `Patient info:` header.
- Both prompts embed the same triage rubric, required fields, and five
  canonical examples (cardiac emergency, non-urgent, missing input, oversized
  input, trauma).

### 1.3 Response pipeline (`services/ai_service.py`)
- `get_triage_recommendation(symptoms, age, gender, model_name=None)` —
  end-to-end entry point used by the views.
- `_parse_ai_json(text)` — primary `json.loads` path with a regex
  `{…}` extraction fallback for older model outputs.
- `normalize_ai_response(data)` — shape-level hygiene only:
  - `priority_level` clamped to `[1, 5]` (default 3).
  - `urgency_score` clamped to `[0, 100]` (default 50).
  - `category` coerced to one of `Cardiac | Respiratory | Trauma |
    Neurological | General` via an alias map.
  - `is_critical` coerced to `bool`.
  - **No** business-rule invariants (e.g., L1⇄critical coupling) — those
    belong to M6.
- Required-field gate: missing any of `priority_level`, `urgency_score`,
  `condition`, `category`, `is_critical`, `explanation` returns an error dict
  rather than a partially-filled record.
- `normalize_age(value)` → `int` in `[0, 150]` or `None`.
- `normalize_gender(value)` → `male | female | other | unknown` or `None`.

### 1.4 Views (`views.py`)
Three endpoints are wired:
- `POST /api/v1/triage/ai/` — `TriageAIView` — JSON symptom triage.
- `POST /api/v1/triage/pdf-extract/` — `TriagePDFExtractView` — multipart
  PDF upload, text extraction via `PyPDF2`, then AI triage.
- `POST /api/v1/triage/evaluate/` — `TriageEvaluateView` — thin M6 placeholder
  that proxies through `services/triage_service.py`.

Both AI endpoints surface failures as clean HTTP error codes (no rule-based
substitution here — that's M6's job):
- `502 BAD_GATEWAY` — unhandled exception from the Gemini client layer.
- `503 SERVICE_UNAVAILABLE` — AI returned a structured error envelope
  (all models failed, circuit open, invalid JSON, missing required field).
- `500 INTERNAL_SERVER_ERROR` — AI response failed schema validation.
- `400 BAD_REQUEST` — input validation (missing/too long/irrelevant symptoms,
  missing/empty/non-PDF/irrelevant PDF, >5 MB upload).

### 1.5 Serializers (`serializers.py`)
- `TriageUserInputSerializer` — `symptoms` (required), `age`, `gender`.
- `TriageAIResponseSerializer` — the canonical response schema (see §3).
- `PDFUploadSerializer` — `.pdf` extension + 5 MB size cap.

---

## 2. Configuration

All AI-layer behavior is environment-tunable (defined in `config/settings.py`):

| Setting | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | API key for `google.generativeai`. |
| `GEMINI_MAX_RETRIES` | `2` | Attempts per model before moving on. |
| `GEMINI_TIMEOUT_SECONDS` | `8` | Per-call wall-clock budget. |
| `GEMINI_MODEL_PRIORITY` | `gemini-2.5-flash,gemini-1.5-flash` | Comma-separated allow-list, tried in order. |
| `GEMINI_MODEL_LIST_TTL_SECONDS` | `600` | Cache TTL for `list_models()`. |
| `GEMINI_CIRCUIT_BREAKER_THRESHOLD` | `5` | Consecutive failures before circuit opens. |
| `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS` | `30` | Time the circuit stays open. |

---

## 3. Public Surface

| Symbol | Module | Description |
|---|---|---|
| `get_triage_recommendation` | `services.ai_service` | Main entry: prompt → Gemini → parsed/normalized dict or error dict. |
| `call_gemini_api` | `services.ai_service` | Low-level model-list-aware call with retry/timeout/breaker. |
| `normalize_ai_response` | `services.ai_service` | Schema-hygiene on a raw AI dict. |
| `normalize_age` / `normalize_gender` | `services.ai_service` | Demographic coercion. |
| `invalidate_model_list_cache` | `services.ai_service` | Clear the cached model list. |
| `reset_circuit_breaker` | `services.ai_service` | Clear breaker state. |
| `build_triage_prompt` | `services.prompt_engine` | Symptom-text prompt. |
| `build_pdf_triage_prompt` | `services.prompt_engine` | PDF-text prompt. |
| `TriageAIView` / `TriagePDFExtractView` | `views` | DRF views for the AI endpoints. |

---

## 4. Running & Testing

```powershell
cd Django-Backend
pip install -r triagesync_backend/requirements.txt
python manage.py runserver
python -m pytest triagesync_backend/apps/triage/tests/test_ai_fallback.py -v --tb=short --reuse-db
```

The test module covers every feature listed in §1: multi-model failure paths,
circuit breaker open/close, model-list cache hit count, JSON-mode + markdown
fallback parsing, prompt-injection invariance (tag-count baseline), age/gender
normalization, category alias mapping, clamp ranges, PDF demographics, and
the three view-level error surfaces (502 / 503 / 500).

---

## 5. Non-Goals (handled by Member 6)

The following are explicitly **not** part of M5 and must be implemented by M6
in `services/triage_service.py`:

- Priority ↔ is_critical coupling rules (e.g., L1 implies critical).
- Rule-based fallback substitution when the AI is unavailable.
- Urgency-score policy beyond range clamping.
- Final decision on whether a 503 AI error should be replaced with a
  keyword-matched rule-based result before returning to the patient.

See `Task Classification.md` for the full ownership matrix.
