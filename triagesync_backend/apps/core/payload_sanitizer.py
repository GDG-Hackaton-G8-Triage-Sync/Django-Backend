import re
import json

# List of allowed fields to send to LLM
ALLOWED_FIELDS = {"age", "gender", "symptoms"}

def extract_warnings_and_validate(data):
    """
    Returns (sanitized_data, warning, error):
    - warning: if age or gender missing
    - error: if symptoms missing or empty
    """
    sanitized = sanitize_payload(data)
    # Symptoms must be present and non-empty (as a string)
    symptoms = sanitized.get("symptoms")
    if not symptoms or (isinstance(symptoms, str) and not symptoms.strip()):
        return sanitized, None, "At least one symptom must be provided."
    warning = None
    if not sanitized.get("age") or not sanitized.get("gender"):
        warning = "Important data (age or gender) is missing. Only symptoms will be used."
    return sanitized, warning, None

def sanitize_payload(data):
    """
    Remove all PII from the payload, only allow age, gender, symptoms.
    Works for dicts, lists, and nested structures.
    """
    if isinstance(data, dict):
        return {k: sanitize_payload(v) for k, v in data.items() if k in ALLOWED_FIELDS}
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    else:
        return data

class PayloadSanitizerMiddleware:
    """
    Django middleware to sanitize request payloads before LLM processing.
    Only allows age, gender, symptoms fields.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only sanitize for API endpoints that send data to LLM
        if request.path.startswith("/api/v1/triage/") and request.method in ("POST", "PUT", "PATCH"):
            try:
                if request.content_type and "application/json" in request.content_type:
                    body_unicode = request.body.decode("utf-8")
                    if body_unicode:
                        data = json.loads(body_unicode)
                        sanitized, warning, error = extract_warnings_and_validate(data)
                        # Attach warning/error to request for downstream use
                        request._triage_warning = warning
                        request._triage_error = error
                        # Replace request._body and request.body with sanitized JSON
                        request._body = json.dumps(sanitized).encode("utf-8")
                        request.body = request._body
            except Exception:
                pass
        response = self.get_response(request)
        return response
