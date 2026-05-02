import os
import json
import re
import time
import logging
import threading
import concurrent.futures
import google.generativeai as genai
from .prompt_engine import build_triage_prompt

# Ensure GEMINI_API_KEY is set in environment
if not os.environ.get("GEMINI_API_KEY"):
    try:
        from django.conf import settings
        os.environ["GEMINI_API_KEY"] = getattr(settings, "GEMINI_API_KEY", "")
    except ImportError:
        pass

DEFAULT_MODEL_NAME = "gemini-2.5-flash"
logger = logging.getLogger("triage.ai")

# Gemini JSON mode -- forces the model to emit a single valid JSON object and
# removes the need for markdown-fence stripping / single-quote hacks downstream.
_JSON_GENERATION_CONFIG = {"response_mime_type": "application/json"}


def _get_setting(name, default):
    """Read a Django setting with a safe fallback when settings aren't loaded."""
    try:
        from django.conf import settings as _s
        return getattr(_s, name, default)
    except Exception:
        return default


# --- Cached model discovery ------------------------------------------------
# list_models() is a network round-trip to Google; caching it per-process for
# a few minutes avoids hitting it on every triage request.
_model_list_cache = {"expiry": 0.0, "names": None}
_model_list_lock = threading.Lock()


def _resolve_model_priority(requested_model=None):
    """Return an ordered list of model names to try, constrained to the
    configured allow-list and (when available) intersected with the set of
    models actually enabled for this API key."""
    priority = list(_get_setting("GEMINI_MODEL_PRIORITY", ["gemini-2.5-flash", "gemini-1.5-flash"]))
    if requested_model and requested_model not in priority:
        priority.insert(0, requested_model)

    ttl = _get_setting("GEMINI_MODEL_LIST_TTL_SECONDS", 600)
    now = time.monotonic()
    with _model_list_lock:
        cached = _model_list_cache["names"]
        if cached is None or _model_list_cache["expiry"] <= now:
            try:
                available = {
                    m.name for m in genai.list_models()
                    if hasattr(m, "supported_generation_methods")
                    and "generateContent" in m.supported_generation_methods
                }
                _model_list_cache["names"] = available
                _model_list_cache["expiry"] = now + ttl
                logger.info("[Gemini] Refreshed model list cache (%d models, ttl=%ss)", len(available), ttl)
                cached = available
            except Exception as e:
                logger.error("[Gemini] list_models() failed: %s", e)
                # Keep stale cache if present; otherwise skip intersection.

    if not cached:
        return priority  # best-effort: trust the configured allow-list

    # Match either form Gemini returns ("models/gemini-1.5-flash" vs "gemini-1.5-flash")
    short_to_full = {n.split("/")[-1]: n for n in cached}
    resolved = []
    for name in priority:
        short = name.split("/")[-1]
        if name in cached:
            resolved.append(name)
        elif short in short_to_full:
            resolved.append(short_to_full[short])
    return resolved or priority


def invalidate_model_list_cache():
    """Test / ops hook: force a refresh of the list_models() cache."""
    with _model_list_lock:
        _model_list_cache["names"] = None
        _model_list_cache["expiry"] = 0.0


# --- Circuit breaker -------------------------------------------------------
class _CircuitBreaker:
    """After `threshold` consecutive full-call failures, short-circuit to
    the fallback for `cooldown` seconds. Any success resets the counter."""

    def __init__(self):
        self.consecutive_failures = 0
        self.open_until = 0.0
        self.lock = threading.Lock()

    def allow(self):
        with self.lock:
            return time.monotonic() >= self.open_until

    def record_success(self):
        with self.lock:
            self.consecutive_failures = 0
            self.open_until = 0.0

    def record_failure(self):
        with self.lock:
            self.consecutive_failures += 1
            threshold = _get_setting("GEMINI_CIRCUIT_BREAKER_THRESHOLD", 5)
            cooldown = _get_setting("GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS", 30)
            if self.consecutive_failures >= threshold:
                self.open_until = time.monotonic() + cooldown
                logger.warning(
                    "[Gemini] Circuit breaker opened for %ss after %d consecutive failures",
                    cooldown, self.consecutive_failures,
                )

    def reset(self):
        with self.lock:
            self.consecutive_failures = 0
            self.open_until = 0.0


_circuit_breaker = _CircuitBreaker()


def reset_circuit_breaker():
    """Test / ops hook to clear circuit breaker state."""
    _circuit_breaker.reset()


# --- Demographic normalization --------------------------------------------
_GENDER_MAP = {
    "m": "male", "male": "male", "man": "male", "boy": "male",
    "f": "female", "female": "female", "woman": "female", "girl": "female",
    "o": "other", "other": "other", "nonbinary": "other", "non-binary": "other", "nb": "other",
    "u": "unknown", "unknown": "unknown", "prefer not to say": "unknown", "n/a": "unknown",
}

_BLOOD_TYPE_MAP = {
    "a+": "A+", "a positive": "A+", "a pos": "A+", "a +": "A+",
    "a-": "A-", "a negative": "A-", "a neg": "A-", "a -": "A-",
    "b+": "B+", "b positive": "B+", "b pos": "B+", "b +": "B+",
    "b-": "B-", "b negative": "B-", "b neg": "B-", "b -": "B-",
    "ab+": "AB+", "ab positive": "AB+", "ab pos": "AB+", "ab +": "AB+",
    "ab-": "AB-", "ab negative": "AB-", "ab neg": "AB-", "ab -": "AB-",
    "o+": "O+", "o positive": "O+", "o pos": "O+", "o +": "O+",
    "o-": "O-", "o negative": "O-", "o neg": "O-", "o -": "O-",
}


def normalize_age(age):
    """Coerce to int in [0, 150]; anything else -> None (prompt says 'unknown')."""
    try:
        n = int(age)
    except (TypeError, ValueError):
        return None
    if n < 0 or n > 150:
        return None
    return n


def normalize_gender(gender):
    """Canonicalize to {'male','female','other','unknown'} or None if blank."""
    if gender is None:
        return None
    s = str(gender).strip().lower()
    if not s:
        return None
    return _GENDER_MAP.get(s, "other")


def normalize_blood_type(blood_type):
    """Canonicalize to standard blood type format or None if blank/invalid."""
    if blood_type is None:
        return None
    s = str(blood_type).strip().lower()
    if not s:
        return None
    return _BLOOD_TYPE_MAP.get(s, None)  # Invalid → None


# --- Error classification --------------------------------------------------
# Single source of truth for mapping a raw exception string to an error
# category. Previously the classification lived in two separate spots (per
# attempt in retry_model and again in the final aggregation loop), each doing
# its own substring match. One helper + one label map keeps them in sync.
_ERROR_LABELS = {
    "quota": "Quota exceeded or out of limit",
    "not_found": "Model not found or not enabled",
    "other": "Other error",
}


def _classify_model_error(err_str):
    s = (err_str or "").lower()
    if "quota" in s or "exceeded" in s:
        return "quota"
    if "404" in s or "not found" in s:
        return "not_found"
    return "other"


# --- Gemini call -----------------------------------------------------------
def call_gemini_api(prompt, model_name=None, user_description=None):
    """Run `prompt` through the configured model priority list with retries,
    timeout, and circuit-breaker protection. Returns the raw response text
    from the first successful model, or a JSON error envelope on failure."""
    # Short-circuit when the breaker is open -- no quota wasted, no latency spent.
    if not _circuit_breaker.allow():
        logger.warning("[Gemini] Circuit breaker open; skipping AI call.")
        return json.dumps({
            "error": "AI unavailable, staff review required",
            "user_description": user_description,
            "details": ["Circuit breaker open after consecutive failures"],
            "error_types": ["circuit_open"],
        })

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    errors = []
    error_types = set()
    max_retries = _get_setting("GEMINI_MAX_RETRIES", 2)
    configured_timeout = _get_setting("GEMINI_TIMEOUT_SECONDS", 30)
    # Safety floor: historical bug reports showed 8s timing out valid AI calls.
    # Keep settings support, but never go below the minimum operational timeout.
    min_timeout_seconds = _get_setting("GEMINI_MIN_TIMEOUT_SECONDS", 30)
    timeout_seconds = max(configured_timeout, min_timeout_seconds)

    def try_generate(model, prompt):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(model.generate_content, prompt)
            try:
                return future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Timeout after {timeout_seconds}s")

    def retry_model(model_name, prompt):
        for attempt in range(1, max_retries + 1):
            try:
                model = genai.GenerativeModel(
                    model_name,
                    generation_config=_JSON_GENERATION_CONFIG,
                )
                response = try_generate(model, prompt)
                return response.text
            except Exception as e:
                err_type = _classify_model_error(str(e))
                errors.append(f"{model_name} (attempt {attempt}): {_ERROR_LABELS[err_type]}: {e}")
                error_types.add(err_type)
                # Deterministic failures won't clear on an immediate retry --
                # skip the remaining attempts and fall through to the next model.
                if err_type in ("quota", "not_found"):
                    return None
                time.sleep(2 ** (attempt - 1))
        return None

    model_priority = _resolve_model_priority(model_name)
    logger.info("[Gemini] Model fallback order: %s", model_priority)
    for m in model_priority:
        logger.info("[Gemini] Trying model: %s", m)
        result = retry_model(m, prompt)
        if result:
            logger.info("[Gemini] Model %s succeeded.", m)
            _circuit_breaker.record_success()
            return result
        logger.warning("[Gemini] Model %s failed.", m)

    _circuit_breaker.record_failure()
    return json.dumps({
        "error": "AI unavailable, staff review required",
        "user_description": user_description,
        "details": errors,
        "error_types": list(error_types),
    })


# ---------------------------------------------------------------------------
# Response normalization
# ---------------------------------------------------------------------------
# AI output can drift (bad enums, out-of-range ints, inconsistent flags). We
# clamp / normalize here before handing the dict back to the view so downstream
# serializer validation and queue ordering see a well-formed, invariant-holding
# record.

_ALLOWED_CATEGORIES = ("Cardiac", "Respiratory", "Trauma", "Neurological", "General")

_CATEGORY_ALIASES = {
    "cardiac": "Cardiac", "cardiovascular": "Cardiac", "cardio": "Cardiac", "heart": "Cardiac",
    "respiratory": "Respiratory", "pulmonary": "Respiratory", "lung": "Respiratory", "breathing": "Respiratory",
    "trauma": "Trauma", "injury": "Trauma", "musculoskeletal": "Trauma", "orthopedic": "Trauma",
    "neurological": "Neurological", "neuro": "Neurological", "neurology": "Neurological", "stroke": "Neurological",
    "general": "General",
}

_REQUIRED_FIELDS = ("priority_level", "urgency_score", "condition", "category", "is_critical", "explanation")


def _clamp_int(value, lo, hi, default):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _normalize_category(value):
    if isinstance(value, str):
        v = value.strip()
        if v in _ALLOWED_CATEGORIES:
            return v
        return _CATEGORY_ALIASES.get(v.lower(), "General")
    return "General"


def normalize_ai_response(data):
    """Shape-level hygiene on the AI's raw dict so it satisfies the response
    serializer. Scope is limited to M5 concerns:
      * priority_level clamped to [1,5]; urgency_score clamped to [0,100]
      * category coerced to one of the 5 allowed enum values
      * is_critical coerced to bool
      * confidence clamped to [0.0, 1.0]

    Business-rule coupling between priority_level and is_critical
    (e.g., L1<->critical invariants, criticality-driven priority clamping)
    is intentionally NOT applied here -- that logic lives in the M6 triage
    service alongside urgency scoring and priority mapping.
    """
    if not isinstance(data, dict) or "error" in data:
        return data

    data["priority_level"] = _clamp_int(data.get("priority_level"), 1, 5, 3)
    data["urgency_score"] = _clamp_int(data.get("urgency_score"), 0, 100, 50)
    data["category"] = _normalize_category(data.get("category"))
    data["is_critical"] = bool(data.get("is_critical"))
    
    # Handle confidence
    try:
        conf = float(data.get("confidence", 0.0))
        data["confidence"] = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        data["confidence"] = 0.0
        
    return data


def _parse_ai_json(text):
    """Parse a JSON object from Gemini output. JSON mode should give clean JSON,
    but we keep a defensive regex-extraction path for older models / edge cases."""
    try:
        return json.loads(text), None
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0)), None
        except Exception as e:
            return None, str(e)
    return None, "no JSON object found"


def get_triage_recommendation(symptoms, age=None, gender=None, blood_type=None, model_name=None, patient_context=None):
    age = normalize_age(age)
    gender = normalize_gender(gender)
    blood_type = normalize_blood_type(blood_type)
    prompt = build_triage_prompt(
        symptoms,
        age=age,
        gender=gender,
        blood_type=blood_type,
        patient_context=patient_context,
    )
    response_text = call_gemini_api(prompt, model_name=model_name, user_description=symptoms)
    logger.debug("Raw AI response: %r", response_text)

    # If Gemini returns a JSON error summary from call_gemini_api, pass it through
    try:
        error_obj = json.loads(response_text)
        if isinstance(error_obj, dict) and "error" in error_obj:
            return error_obj
    except Exception:
        pass

    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`\n ")
    logger.debug("Cleaned AI response: %r", cleaned)

    data, parse_err = _parse_ai_json(cleaned)
    if data is None:
        return {"error": "AI response is not valid JSON", "raw": cleaned, "parse_error": parse_err}

    data.pop("priority", None)  # legacy string priority, ignored
    for field in _REQUIRED_FIELDS:
        if field not in data:
            return {"error": f"'{field}' field missing in AI response", "raw": cleaned}

    return normalize_ai_response(data)


"""
AI service — infers an urgency score (0-100) from symptom text.

Returns an integer score that maps to priority levels via PRIORITY_THRESHOLDS.
The output schema matches the API contract:
    {"priority": int, "urgency_score": int, "condition": str}
"""


# Keyword → (urgency_score, condition) mapping
_SYMPTOM_RULES = [
    (["chest pain", "heart attack", "cardiac"], 95, "Cardiac Event"),
    (["no breathing", "not breathing", "stopped breathing"], 95, "Respiratory Arrest"),
    (["unconscious", "unresponsive"], 90, "Loss of Consciousness"),
    (["severe bleeding", "heavy bleeding"], 88, "Severe Hemorrhage"),
    (["stroke", "facial droop", "slurred speech"], 92, "Stroke"),
    (["seizure", "convulsion"], 85, "Seizure"),
    (["high fever", "fever above 40", "fever above 39"], 70, "High Fever"),
    (["fever", "temperature"], 65, "Fever"),
    (["severe pain", "extreme pain"], 68, "Severe Pain"),
    (["dizzy", "dizziness", "lightheaded"], 55, "Dizziness"),
    (["pain", "ache", "aching"], 50, "Pain"),
    (["nausea", "vomiting"], 45, "Nausea/Vomiting"),
    (["cough", "cold", "runny nose"], 30, "Minor Respiratory"),
]


def infer_priority(symptoms: str) -> dict:
    """
    Analyse symptom text and return an AI output dict.

    Returns:
        {"priority": int, "urgency_score": int, "condition": str}
    """
    text = symptoms.lower()

    for keywords, score, condition in _SYMPTOM_RULES:
        if any(kw in text for kw in keywords):
            priority = _score_to_priority(score)
            return {
                "priority": priority,
                "urgency_score": score,
                "condition": condition,
            }

    # Default — low urgency
    return {
        "priority": 5,
        "urgency_score": 15,
        "condition": "General Complaint",
    }


def _score_to_priority(score: int) -> int:
    """Convert urgency score to priority level 1-5."""
    if score >= 80:
        return 1
    if score >= 60:
        return 2
    if score >= 40:
        return 3
    if score >= 20:
        return 4
    return 5
