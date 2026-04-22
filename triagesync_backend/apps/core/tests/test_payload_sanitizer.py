import pytest
from django.test import RequestFactory
from triagesync_backend.apps.core.payload_sanitizer import sanitize_payload, PayloadSanitizerMiddleware

def test_sanitize_payload_removes_pii():
    data = {
        "name": "John Doe",
        "age": 30,
        "gender": "M",
        "symptoms": "headache",
        "address": "123 Main St",
        "phone": "555-1234",
        "extra": {"ssn": "123-45-6789", "symptoms": "nausea"}
    }
    sanitized = sanitize_payload(data)
    assert sanitized == {"age": 30, "gender": "M", "symptoms": "headache"}

def test_sanitize_payload_nested_list():
    data = {"age": 40, "symptoms": ["cough", {"name": "Jane", "symptoms": "fever"}]}
    sanitized = sanitize_payload(data)
    assert sanitized == {"age": 40, "symptoms": ["cough", {"symptoms": "fever"}]}

def test_middleware_sanitizes_request(monkeypatch):
    factory = RequestFactory()
    data = {
        "name": "Alice",
        "age": 25,
        "gender": "F",
        "symptoms": "dizziness"
    }
    import json
    request = factory.post("/api/v1/triage/ai/", data=json.dumps(data), content_type="application/json")
    # Patch get_response to just return a dummy response
    def dummy_response(req):
        return req
    middleware = PayloadSanitizerMiddleware(dummy_response)
    sanitized_request = middleware(request)
    sanitized_data = json.loads(sanitized_request.body.decode("utf-8"))
    assert sanitized_data == {"age": 25, "gender": "F", "symptoms": "dizziness"}
