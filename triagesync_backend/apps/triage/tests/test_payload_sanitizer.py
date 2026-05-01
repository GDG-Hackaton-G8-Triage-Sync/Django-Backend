"""Unit tests for the triage payload sanitizer middleware.

These tests exercise the middleware directly via Django's RequestFactory so
they require no DB, no AI calls, and no DRF view dispatch.
"""
import json

import pytest
from django.test import RequestFactory

from triagesync_backend.apps.core.middleware.payload_sanitizer import (
    MAX_SYMPTOMS_LENGTH,
    PayloadSanitizerMiddleware,
)


def _run(request):
    """Invoke the middleware and return the response sentinel."""
    sentinel = object()
    mw = PayloadSanitizerMiddleware(get_response=lambda _r: sentinel)
    return mw(request), sentinel


def _post_json(path, body):
    rf = RequestFactory()
    return rf.post(path, data=json.dumps(body), content_type="application/json")


def test_strips_disallowed_keys():
    req = _post_json(
        "/api/v1/triage/ai/",
        {"symptoms": "chest pain", "age": 50, "gender": "M",
         "ssn": "123-45-6789", "email": "x@y.z"},
    )
    _run(req)
    sanitized = json.loads(req.body)
    assert set(sanitized.keys()) == {"symptoms", "age", "gender"}
    assert "ssn" not in sanitized
    assert "email" not in sanitized


def test_whitelisted_values_preserved():
    req = _post_json(
        "/api/v1/triage/ai/",
        {"symptoms": "fever and cough", "age": 30, "gender": "F", "blood_type": "A+"},
    )
    _run(req)
    sanitized = json.loads(req.body)
    assert sanitized["symptoms"] == "fever and cough"
    assert sanitized["age"] == 30
    assert sanitized["gender"] == "F"
    assert sanitized["blood_type"] == "A+"
    assert not hasattr(req, "_triage_error")
    assert not hasattr(req, "_triage_warning")


def test_non_triage_path_bypassed():
    rf = RequestFactory()
    body = json.dumps({"symptoms": "x", "ssn": "leak"})
    req = rf.post("/api/v1/patients/", data=body, content_type="application/json")
    _run(req)
    untouched = json.loads(req.body)
    assert "ssn" in untouched


def test_get_request_bypassed():
    rf = RequestFactory()
    req = rf.get("/api/v1/triage/ai/")
    _run(req)
    assert not hasattr(req, "_triage_error")
    assert not hasattr(req, "_triage_warning")


def test_multipart_bypassed():
    rf = RequestFactory()
    req = rf.post(
        "/api/v1/triage/pdf-extract/",
        data={"file": "binary"},
    )
    _run(req)
    assert not hasattr(req, "_triage_error")


def test_missing_symptoms_sets_error():
    req = _post_json("/api/v1/triage/ai/", {"age": 40, "gender": "M"})
    _run(req)
    assert getattr(req, "_triage_error", None) == "missing_symptoms"


def test_empty_symptoms_sets_error():
    req = _post_json("/api/v1/triage/ai/", {"symptoms": "   ", "age": 40, "gender": "M"})
    _run(req)
    assert getattr(req, "_triage_error", None) == "missing_symptoms"


def test_missing_age_sets_warning():
    req = _post_json("/api/v1/triage/ai/", {"symptoms": "headache", "gender": "F"})
    _run(req)
    warnings = getattr(req, "_triage_warning", [])
    assert "age_missing" in warnings
    assert "gender_missing" not in warnings


def test_missing_gender_sets_warning():
    req = _post_json("/api/v1/triage/ai/", {"symptoms": "headache", "age": 25})
    _run(req)
    warnings = getattr(req, "_triage_warning", [])
    assert "gender_missing" in warnings
    assert "age_missing" not in warnings


def test_both_demographics_missing_lists_both_warnings():
    req = _post_json("/api/v1/triage/ai/", {"symptoms": "dizzy"})
    _run(req)
    warnings = getattr(req, "_triage_warning", [])
    assert set(warnings) == {"age_missing", "gender_missing", "blood_type_missing"}


def test_control_chars_stripped():
    req = _post_json(
        "/api/v1/triage/ai/",
        {"symptoms": "chest\x00 pain\x07", "age": 50, "gender": "M"},
    )
    _run(req)
    sanitized = json.loads(req.body)
    assert sanitized["symptoms"] == "chest pain"


def test_symptoms_length_capped():
    long_text = "a" * (MAX_SYMPTOMS_LENGTH + 100)
    req = _post_json(
        "/api/v1/triage/ai/",
        {"symptoms": long_text, "age": 50, "gender": "M"},
    )
    _run(req)
    sanitized = json.loads(req.body)
    assert len(sanitized["symptoms"]) == MAX_SYMPTOMS_LENGTH


def test_invalid_json_sets_error():
    rf = RequestFactory()
    req = rf.post(
        "/api/v1/triage/ai/", data="{not valid json}", content_type="application/json"
    )
    _run(req)
    assert getattr(req, "_triage_error", None) == "invalid_json"


def test_non_dict_payload_sets_error():
    req = _post_json("/api/v1/triage/ai/", ["a", "list", "not", "a", "dict"])
    _run(req)
    assert getattr(req, "_triage_error", None) == "invalid_payload"
