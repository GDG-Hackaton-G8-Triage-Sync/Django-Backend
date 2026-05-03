
import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_T6SiVZDcgz2e@ep-square-firefly-abisf3bt-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture(autouse=True)
def stub_demographic_extractor(monkeypatch):
    monkeypatch.setattr(
        "triagesync_backend.apps.triage.services.demographic_extractor.extract_demographics_from_text",
        lambda text: {"age": None, "gender": None, "blood_type": None, "confidence": "low"},
    )

@pytest.mark.django_db
def test_pdf_extract_irrelevant_pdf():
    client = APIClient()
    url = reverse("triage-ai")
    # PDF with irrelevant content
    pdf_file = make_pdf_with_text("This document is about gardening and has no medical content.")
    resp = client.post(url, {"file": pdf_file}, format="multipart")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.data["error"] == "Missing symptoms prompt."
    assert "current feeling" in resp.data["message"].lower()

def make_pdf_with_text(text: str) -> io.BytesIO:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, text)
    c.save()
    buf.seek(0)
    buf.name = "test.pdf"
    return buf

@pytest.mark.django_db
def test_pdf_extract_success(monkeypatch):
    client = APIClient()
    # Patch Gemini call to return a valid triage JSON
    ai_json = {
        "priority_level": 2,
        "urgency_score": 97,
        "condition": "Cardiac Event",
        "category": "Cardiac",
        "is_critical": True,
        "explanation": ["chest pain"],
        "recommended_action": "Immediate ECG and transfer to ER",
        "reason": "Possible heart attack due to chest pain."
    }

    import json
    monkeypatch.setattr(
        "triagesync_backend.apps.triage.views.call_gemini_api",
        lambda prompt, user_description=None: json.dumps(ai_json),
    )
    url = reverse("triage-ai")
    pdf_file = make_pdf_with_text("45-year-old, chest pain")
    resp = client.post(url, {"file": pdf_file, "symptoms": "chest pain"}, format="multipart")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["priority_level"] == 2
    assert resp.data["category"] == "Cardiac"
    assert resp.data["is_critical"] is True
    assert resp.data["explanation"] == ["chest pain"]
    assert resp.data["recommended_action"] == "Immediate ECG and transfer to ER"
    assert resp.data["reason"].startswith("Possible heart attack")


@pytest.mark.django_db
def test_triage_ai_alias_success(monkeypatch):
    client = APIClient()
    ai_json = {
        "priority_level": 3,
        "urgency_score": 72,
        "condition": "General",
        "category": "General",
        "is_critical": False,
        "explanation": ["headache"],
        "recommended_action": "Rest and hydration",
        "reason": "Symptoms are mild and not immediately concerning."
    }

    import json
    captured = {"prompt": None}

    def fake_call_gemini_api(prompt, user_description=None):
        captured["prompt"] = prompt
        return json.dumps(ai_json)

    monkeypatch.setattr(
        "triagesync_backend.apps.triage.views.call_gemini_api",
        fake_call_gemini_api,
    )
    url = reverse("triage-ai")
    pdf_file = make_pdf_with_text("Patient report with headache")
    image_file = SimpleUploadedFile("rash.png", b"image-bytes", content_type="image/png")
    resp = client.post(
        url,
        {"file": pdf_file, "image": image_file, "prompt": "headache"},
        format="multipart",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["priority_level"] == 3
    assert resp.data["category"] == "General"
    assert resp.data["is_critical"] is False
    assert resp.data["image_name"] == "rash.png"
    # The uploaded image should be persisted and an accessible URL returned
    assert "image_url" in resp.data
    assert resp.data["image_url"]
    assert "rash.png" in resp.data["image_url"]
    assert captured["prompt"] is not None
    assert "rash.png" not in captured["prompt"]
    assert "image-bytes" not in captured["prompt"]

@pytest.mark.django_db
def test_pdf_extract_file_too_large():
    client = APIClient()
    url = reverse("triage-ai")
    big_file = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))
    big_file.name = "big.pdf"
    resp = client.post(url, {"file": big_file}, format="multipart")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "File size must be under 5MB" in str(resp.data)

@pytest.mark.django_db
def test_pdf_extract_not_pdf():
    client = APIClient()
    url = reverse("triage-ai")
    txt_file = io.BytesIO(b"not a pdf")
    txt_file.name = "test.txt"
    resp = client.post(url, {"file": txt_file}, format="multipart")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only PDF files are allowed" in str(resp.data)
