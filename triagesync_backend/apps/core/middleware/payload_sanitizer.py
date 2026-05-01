"""Payload sanitization middleware - moved from triage app to core app.

Owns the input gate to the AI prompt: enforces a strict whitelist of allowed
keys ({age, gender, blood_type, symptoms}) on inbound JSON, strips ASCII control
characters, and caps symptoms length. Sets request-scoped attributes
(``_triage_error``, ``_triage_warning``) that downstream views consume.

Runs only on JSON requests under ``/api/v1/triage/`` -- non-triage paths and
multipart uploads pass through untouched.

This middleware belongs in core/ app per Member 1's responsibilities for
core infrastructure components.
"""
import json
import re
from io import BytesIO

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

ALLOWED_KEYS = frozenset({"age", "gender", "symptoms", "description", "blood_type"})
TRIAGE_PATH_PREFIX = "/api/v1/triage/"
MAX_SYMPTOMS_LENGTH = 500
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH"})

# C0 control chars except \t \n \r, plus DEL (0x7F)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_controls(value):
    if isinstance(value, str):
        return _CONTROL_CHARS_RE.sub("", value).strip()
    return value


class PayloadSanitizerMiddleware:
    """Whitelist + hygiene gate for triage JSON payloads."""

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self._is_coroutine = iscoroutinefunction(get_response)
        if self._is_coroutine:
            markcoroutinefunction(self)

    def __call__(self, request):
        if self._is_coroutine:
            return self.__acall__(request)

        if self._should_sanitize(request):
            self._sanitize(request)
        return self.get_response(request)

    async def __acall__(self, request):
        if self._should_sanitize(request):
            self._sanitize(request)
        return await self.get_response(request)

    def _should_sanitize(self, request):
        if request.method not in MUTATING_METHODS:
            return False
        if not request.path.startswith(TRIAGE_PATH_PREFIX):
            return False
        content_type = (request.content_type or "").lower()
        return "application/json" in content_type

    def _sanitize(self, request):
        try:
            raw = request.body
        except Exception:
            request._triage_error = "unreadable_body"
            return

        if not raw:
            request._triage_error = "missing_symptoms"
            return

        try:
            payload = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            request._triage_error = "invalid_json"
            return

        if not isinstance(payload, dict):
            request._triage_error = "invalid_payload"
            return

        sanitized = {k: payload[k] for k in payload if k in ALLOWED_KEYS}
        for key, value in list(sanitized.items()):
            sanitized[key] = _strip_controls(value)

        symptoms = sanitized.get("symptoms")
        if isinstance(symptoms, str) and len(symptoms) > MAX_SYMPTOMS_LENGTH:
            sanitized["symptoms"] = symptoms[:MAX_SYMPTOMS_LENGTH]

        if not sanitized.get("symptoms") and not sanitized.get("description"):
            request._triage_error = "missing_symptoms"

        warnings = []
        if sanitized.get("age") in (None, ""):
            warnings.append("age_missing")
        if sanitized.get("gender") in (None, ""):
            warnings.append("gender_missing")
        if sanitized.get("blood_type") in (None, ""):
            warnings.append("blood_type_missing")
        if warnings:
            request._triage_warning = warnings

        new_body = json.dumps(sanitized).encode("utf-8")
        request._body = new_body
        request._stream = BytesIO(new_body)
        if hasattr(request, "_read_started"):
            request._read_started = False