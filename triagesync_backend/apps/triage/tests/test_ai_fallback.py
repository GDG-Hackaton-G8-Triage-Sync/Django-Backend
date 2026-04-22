import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
def test_ai_irrelevant_text():
    client = APIClient()
    # Irrelevant text (not related to medical/triage)
    resp = client.post(reverse("triage-ai"), {"symptoms": "I like sunny days and reading books."}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Input not relevant."
    assert "provide symptoms or information related" in resp.data["message"].lower()

# Test fallback and error handling for the /api/v1/triage/ai/ endpoint
@pytest.mark.django_db
def test_ai_success(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to return a valid AI response
    from triagesync_backend.apps.triage import views
    monkeypatch.setattr(
        views,
        "get_triage_recommendation",
        lambda symptoms, age=None, gender=None: {
            "priority_level": 1,
            "urgency_score": 97,
            "condition": "Cardiac Event",
            "category": "Cardiac",
            "is_critical": True,
            "explanation": ["chest pain", "sweating"],
            "recommended_action": "Immediate ECG and transfer to ER",
            "reason": "Possible heart attack due to chest pain and risk factors."
        }
    )
    resp = client.post(reverse("triage-ai"), {"symptoms": "chest pain", "age": 45, "gender": "male"}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["priority_level"] == 1
    assert resp.data["condition"] == "Cardiac Event"
    assert resp.data["category"] == "Cardiac"
    assert resp.data["is_critical"] is True
    assert resp.data["explanation"] == ["chest pain", "sweating"]
    assert resp.data["recommended_action"] == "Immediate ECG and transfer to ER"
    assert resp.data["reason"] == "Possible heart attack due to chest pain and risk factors."

@pytest.mark.django_db
def test_ai_all_models_fail(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate all models failing
    from triagesync_backend.apps.triage import views
    monkeypatch.setattr(
        views,
        "get_triage_recommendation",
        lambda symptoms, age=None, gender=None: {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-2.5-flash: Quota exceeded"],
            "error_types": ["quota"]
        }
    )
    resp = client.post(reverse("triage-ai"), {"symptoms": "chest pain", "age": 45, "gender": "male"}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["source"] == "fallback_keyword"
    assert resp.data["is_critical"] is True
    assert resp.data["priority_level"] == 2
    assert resp.data["category"] == "Cardiac"
    assert "quota" in str(resp.data.get("ai_details", [])).lower()

@pytest.mark.django_db
def test_ai_model_not_found(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate model not found error
    from triagesync_backend.apps.triage import views
    monkeypatch.setattr(
        views,
        "get_triage_recommendation",
        lambda symptoms, age=None, gender=None: {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-1.5-flash: Model not found or not enabled"],
            "error_types": ["not_found"]
        }
    )
    resp = client.post(reverse("triage-ai"), {"symptoms": "chest pain", "age": 45, "gender": "male"}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["source"] == "fallback_keyword"
    assert resp.data["is_critical"] is True
    assert resp.data["priority_level"] == 2
    assert "not found" in str(resp.data.get("ai_details", [])).lower()

@pytest.mark.django_db
def test_ai_other_error(monkeypatch):
    client = APIClient()
    # Patch get_triage_recommendation to simulate a generic error
    from triagesync_backend.apps.triage import views
    monkeypatch.setattr(
        views,
        "get_triage_recommendation",
        lambda symptoms, age=None, gender=None: {
            "error": "AI unavailable, staff review required",
            "user_description": "test",
            "details": ["gemini-2.5-flash: Other error: network timeout"],
            "error_types": ["other"]
        }
    )
    resp = client.post(reverse("triage-ai"), {"symptoms": "chest pain", "age": 45, "gender": "male"}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["source"] == "fallback_keyword"
    assert resp.data["is_critical"] is True
    assert resp.data["priority_level"] == 2
    assert "network timeout" in str(resp.data.get("ai_details", [])).lower()

@pytest.mark.django_db
def test_ai_missing_description():
    client = APIClient()
    resp = client.post(reverse("triage-ai"), {}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Missing symptoms."

@pytest.mark.django_db
def test_ai_description_too_long():
    client = APIClient()
    long_symptoms = "a" * 1000
    resp = client.post(reverse("triage-ai"), {"symptoms": long_symptoms, "age": 45, "gender": "male"}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Symptoms too long."
