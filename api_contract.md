# Member 5 — API Contract (Current Format)

Covers only the AI-layer endpoints owned by Member 5. All requests/responses
are JSON unless otherwise noted.

- **Base URL (local):** `http://localhost:8000`
- **Base URL (prod):** `https://django-backend-4r5p.onrender.com`
- **Auth:** none required on these endpoints (permission class is `AllowAny`).

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/triage/ai/` | `POST` | Text-symptom AI triage. |
| `/api/v1/triage/pdf-extract/` | `POST` | PDF-upload AI triage. |
| `/api/v1/triage/evaluate/` | `POST` | Thin M6 placeholder (not documented here). |

---

## 1. `POST /api/v1/triage/ai/`

### 1.1 Request (`application/json`)

```json
{
  "symptoms": "chest pain radiating to left arm, sweating",
  "age": 45,
  "gender": "male"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `symptoms` | string | yes | Max 500 chars. Must contain a relevant medical keyword. |
| `age` | integer | no | Clamped to `[0, 150]`; anything else becomes `unknown`. |
| `gender` | string | no | Canonicalized to `male` / `female` / `other` / `unknown`. |

### 1.2 Success — `200 OK`

```json
{
  "priority_level": 1,
  "urgency_score": 97,
  "condition": "Acute Angina Suspicion",
  "category": "Cardiac",
  "is_critical": true,
  "explanation": ["chest pain", "sweating"],
  "recommended_action": "Immediate ECG and transfer to ER",
  "reason": "Possible heart attack due to chest pain and associated symptoms.",
  "source": "ai"
}
```

Response-field rules (enforced by serializer + `normalize_ai_response`):

| Field | Type | Range / Enum |
|---|---|---|
| `priority_level` | int | `1..5` (1 = most urgent) |
| `urgency_score` | int | `0..100` |
| `condition` | string | short clinical label |
| `category` | enum | `Cardiac` \| `Respiratory` \| `Trauma` \| `Neurological` \| `General` |
| `is_critical` | bool | — |
| `explanation` | list\<string\> | min length 1 |
| `recommended_action` | string | — |
| `reason` | string | 1–2 sentences |
| `source` | string | always `"ai"` for this endpoint |

If the middleware attached a sanitization warning, an optional `"warning"`
key is also included.

### 1.3 Errors

| Status | Trigger | Body |
|---|---|---|
| `400` | `symptoms` missing | `{ "error": "Missing symptoms.", "message": "…" }` |
| `400` | `len(symptoms) > 500` | `{ "error": "Symptoms too long.", "message": "…" }` |
| `400` | Input not medically relevant | `{ "error": "Input not relevant.", "message": "…" }` |
| `502` | Unhandled Gemini client exception | `{ "error": "AI service unavailable.", "message": "…", "details": "<str>" }` |
| `503` | AI error envelope (all models failed / circuit open / invalid JSON / missing field) | `{ "error": "AI unavailable, staff review required", "message": "…", "details": ["gemini-2.5-flash (attempt 1): Quota exceeded …"], "error_types": ["quota"] }` |
| `500` | Serializer validation failed on AI dict | `{ "error": "AI response format error.", "message": "…", "details": <serializer_errors>, "raw_ai": <dict> }` |

`error_types` values: `"quota" | "not_found" | "other" | "circuit_open"`.

---

## 2. `POST /api/v1/triage/pdf-extract/`

### 2.1 Request (`multipart/form-data`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | file | yes | `.pdf` only, ≤ 5 MB. |
| `age` | integer | no | Same handling as §1. |
| `gender` | string | no | Same handling as §1. |

### 2.2 Success — `200 OK`

Identical schema to §1.2 (same serializer). The `source` field is always
`"ai"`. Extracted text is truncated to 10 000 chars before prompting.

### 2.3 Errors

| Status | Trigger | Body |
|---|---|---|
| `400` | Missing / empty file, non-PDF extension, extraction failure, no extractable text, or irrelevant content | `{ "error": "<specific>", "message": "…" }` (see below) |
| `502` | Gemini call or `json.loads` raised | `{ "error": "AI service unavailable.", "message": "…", "details": "<str>" }` |
| `503` | AI error envelope | `{ "error": "AI unavailable, staff review required", "message": "…", "details": [...], "error_types": [...] }` |
| `500` | Serializer validation failed | `{ "error": "AI response format error.", "message": "…", "details": <serializer_errors>, "raw_ai": <dict> }` |

Specific `400` variants:
- `"Empty file."` — zero-byte upload.
- `"Only PDF files are allowed."` — extension not `.pdf`.
- `"PDF extraction failed."` — `PyPDF2` raised; includes `details`.
- `"No text extracted."` — PDF contained no selectable text.
- `"PDF not relevant."` — extracted text lacked medical keywords.

---

## 3. AI Output Contract (internal, between M5 and M6)

After a successful Gemini call, `get_triage_recommendation` returns one of:

**Success shape** — passes `TriageAIResponseSerializer` unchanged:

```json
{
  "priority_level": 1,
  "urgency_score": 97,
  "condition": "Acute Angina Suspicion",
  "category": "Cardiac",
  "is_critical": true,
  "explanation": ["chest pain"],
  "recommended_action": "…",
  "reason": "…"
}
```

**Error shapes** — always carry `"error"` as the discriminator:

```json
{ "error": "AI unavailable, staff review required",
  "user_description": "chest pain",
  "details": ["gemini-2.5-flash (attempt 1): Quota exceeded: …"],
  "error_types": ["quota"] }
```
```json
{ "error": "AI response is not valid JSON",
  "raw": "<cleaned response text>",
  "parse_error": "<jsonlib message>" }
```
```json
{ "error": "'category' field missing in AI response",
  "raw": "<cleaned response text>" }
```

M6 is the consumer that decides whether an error shape should be replaced
with a rule-based result before returning to the patient.

---

## 4. Behavior Guarantees (M5)

- **JSON-only output.** Models are invoked in JSON mode; no markdown fences.
- **Injection-safe prompts.** User content is wrapped in delimiter tags and
  pre-stripped of any tag-like tokens.
- **Bounded latency.** Each model attempt is capped at
  `GEMINI_TIMEOUT_SECONDS` (default 8 s). Worst-case per request on transient
  errors: `len(GEMINI_MODEL_PRIORITY) × GEMINI_MAX_RETRIES × GEMINI_TIMEOUT_SECONDS`.
  Deterministic errors (`quota`, `not_found`) short-circuit the retry loop
  on that model and cascade immediately, so in practice quota-exhausted paths
  are much faster than the worst-case formula suggests.
- **Multi-model resilience.** Default priority covers six free-tier models
  (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.0-flash`,
  `gemini-2.0-flash-lite`, `gemini-1.5-flash`, `gemini-1.5-flash-8b`). Each
  has an independent daily quota, so exhausting one simply cascades to the
  next; models not enabled for the active API key are filtered out at runtime.
- **Cascade protection.** After `GEMINI_CIRCUIT_BREAKER_THRESHOLD` consecutive
  failures, calls short-circuit to a `circuit_open` error envelope for
  `GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`.
- **Schema invariants.** `priority_level ∈ [1,5]`, `urgency_score ∈ [0,100]`,
  `category ∈ {Cardiac, Respiratory, Trauma, Neurological, General}`,
  `is_critical` is always a bool, `explanation` is a non-empty list.
