
from django.test import TestCase
from triagesync_backend.apps.triage.services import triage_service

class TriageLogicTests(TestCase):
    def test_emergency_override(self):
        symptoms = "Patient is unconscious and not breathing."
        response = triage_service.evaluate_triage(symptoms)
        data = response["data"]
        self.assertTrue(data["triage_result"]["priority"] == 1)
        self.assertTrue(data["triage_result"]["is_critical"])
        self.assertEqual(data["ai_contract"]["category"], "General")
        self.assertIn("emergency", data["ai_contract"]["reason"].lower())

    def test_normal_ai_flow(self):
        symptoms = "Patient has mild cough and runny nose."
        response = triage_service.evaluate_triage(symptoms)
        data = response["data"]
        self.assertIn(data["triage_result"]["priority"], [4, 5])
        self.assertFalse(data["triage_result"]["is_critical"])
        self.assertIn("urgency_score", data["ai_contract"])
        self.assertIn("category", data["ai_contract"])

    def test_contract_fields_present(self):
        symptoms = "chest pain radiating to left arm, sweating"
        response = triage_service.evaluate_triage(symptoms)
        data = response["data"]
        contract = data["ai_contract"]
        required_fields = [
            "urgency_score", "category", "explanation", "recommended_action", "reason", "priority_level", "is_critical", "source"
        ]
        for field in required_fields:
            self.assertIn(field, contract)
