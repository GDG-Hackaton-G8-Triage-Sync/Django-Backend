import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Test fallback and error handling for the /api/v1/triage/ai/ endpoint
@pytest.mark.django_db
def test_ai_success(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to return a valid AI response
    with patch("triagesync_backend.apps.triage.views.get_triage_recommendation") as mock_ai:
        mock_ai.return_value = {
            "priority_level": 1,
            "urgency_score": 97,
            "condition": "Cardiac Event",
            "category": "Cardiac",
            "is_critical": True,
            "explanation": ["chest pain", "sweating"]
        }
        resp = client.post(reverse("triage-ai"), {"description": "test"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["priority_level"] == 1
        assert resp.data["condition"] == "Cardiac Event"
        assert resp.data["category"] == "Cardiac"
        assert resp.data["is_critical"] is True
        assert resp.data["explanation"] == ["chest pain", "sweating"]

@pytest.mark.django_db
def test_ai_all_models_fail(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate all models failing
    with patch("triagesync_backend.apps.triage.views.get_triage_recommendation") as mock_ai:
        mock_ai.return_value = {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-2.5-flash: Quota exceeded"],
            "error_types": ["quota"]
        }
        resp = client.post(reverse("triage-ai"), {"description": "test"}, format="json")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert resp.data["error"] == "AI unavailable."
        assert "quota" in str(resp.data["details"]).lower()

@pytest.mark.django_db
def test_ai_model_not_found(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate model not found error
    with patch("triagesync_backend.apps.triage.views.get_triage_recommendation") as mock_ai:
        mock_ai.return_value = {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-1.5-flash: Model not found or not enabled"],
            "error_types": ["not_found"]
        }
        resp = client.post(reverse("triage-ai"), {"description": "test"}, format="json")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert resp.data["error"] == "AI unavailable."
        assert "not found" in str(resp.data["details"]).lower()

@pytest.mark.django_db
def test_ai_other_error(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate a generic error
    with patch("triagesync_backend.apps.triage.views.get_triage_recommendation") as mock_ai:
        mock_ai.return_value = {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-2.5-flash: Other error: network timeout"],
            "error_types": ["other"]
        }
        resp = client.post(reverse("triage-ai"), {"description": "test"}, format="json")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert resp.data["error"] == "AI unavailable."
        assert "network timeout" in str(resp.data["details"]).lower()

@pytest.mark.django_db
def test_ai_missing_description():
    client = APIClient()
    resp = client.post(reverse("triage-ai"), {}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Missing description."

@pytest.mark.django_db
def test_ai_description_too_long():
    client = APIClient()
    long_desc = "a" * 1000
    resp = client.post(reverse("triage-ai"), {"description": long_desc}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Description too long."
