"""
Tests for Member 6 — Triage Logic & Business Rules

Coverage:
- Priority calculation (all 5 levels)
- Configurable thresholds
- Emergency keyword override
- Symptom-based priority (critical symptoms → priority 1)
- AI fallback when output is invalid or AI raises exception
- Critical alert broadcast triggered for priority 1
- priority_update broadcast triggered for all cases
- Full evaluate_triage() integration
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from triagesync_backend.apps.triage.services.triage_service import (
    calculate_priority,
    check_emergency_override,
    evaluate_triage,
    process_triage,
    safe_infer_priority,
)
from triagesync_backend.apps.triage.services.validation_service import (
    get_fallback_ai_output,
    validate_ai_output,
    validate_symptoms,
)

CUSTOM_THRESHOLDS = {
    "critical": 80,
    "high": 60,
    "medium": 40,
    "low": 20,
}

CUSTOM_FALLBACK = {
    "priority": 3,
    "urgency_score": 50,
    "condition": "Unknown",
}


# ─────────────────────────────────────────────
# validate_symptoms
# ─────────────────────────────────────────────
class ValidateSymptomsTests(TestCase):

    def test_valid_symptoms_returned_clean(self):
        self.assertEqual(validate_symptoms("  fever  "), "fever")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            validate_symptoms("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            validate_symptoms("   ")

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            validate_symptoms(None)


# ─────────────────────────────────────────────
# validate_ai_output
# ─────────────────────────────────────────────
class ValidateAiOutputTests(TestCase):

    def test_valid_output_passes(self):
        self.assertTrue(validate_ai_output({
            "priority": 1, "urgency_score": 95, "condition": "Cardiac Event"
        }))

    def test_missing_key_fails(self):
        self.assertFalse(validate_ai_output({"priority": 1, "urgency_score": 95}))

    def test_score_out_of_range_fails(self):
        self.assertFalse(validate_ai_output({
            "priority": 1, "urgency_score": 150, "condition": "X"
        }))

    def test_invalid_priority_fails(self):
        self.assertFalse(validate_ai_output({
            "priority": 0, "urgency_score": 50, "condition": "X"
        }))

    def test_non_dict_fails(self):
        self.assertFalse(validate_ai_output("not a dict"))


# ─────────────────────────────────────────────
# get_fallback_ai_output
# ─────────────────────────────────────────────
class FallbackAiOutputTests(TestCase):

    @override_settings(TRIAGE_FALLBACK=CUSTOM_FALLBACK)
    def test_fallback_uses_settings(self):
        fallback = get_fallback_ai_output()
        self.assertEqual(fallback["priority"], 3)
        self.assertEqual(fallback["urgency_score"], 50)
        self.assertEqual(fallback["condition"], "Unknown")


# ─────────────────────────────────────────────
# calculate_priority — all 5 levels
# ─────────────────────────────────────────────
class CalculatePriorityTests(TestCase):

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_100_is_priority_1(self):
        self.assertEqual(calculate_priority(100), 1)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_80_is_priority_1(self):
        self.assertEqual(calculate_priority(80), 1)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_79_is_priority_2(self):
        self.assertEqual(calculate_priority(79), 2)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_60_is_priority_2(self):
        self.assertEqual(calculate_priority(60), 2)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_59_is_priority_3(self):
        self.assertEqual(calculate_priority(59), 3)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_40_is_priority_3(self):
        self.assertEqual(calculate_priority(40), 3)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_39_is_priority_4(self):
        self.assertEqual(calculate_priority(39), 4)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_20_is_priority_4(self):
        self.assertEqual(calculate_priority(20), 4)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_19_is_priority_5(self):
        self.assertEqual(calculate_priority(19), 5)

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_score_0_is_priority_5(self):
        self.assertEqual(calculate_priority(0), 5)


# ─────────────────────────────────────────────
# check_emergency_override
# ─────────────────────────────────────────────
class EmergencyOverrideTests(TestCase):

    def test_chest_pain_triggers_override(self):
        result = check_emergency_override("Patient has chest pain and sweating")
        self.assertTrue(result["override"])
        self.assertEqual(result["urgency_score"], 100)

    def test_stroke_triggers_override(self):
        result = check_emergency_override("Possible stroke, facial droop")
        self.assertTrue(result["override"])

    def test_heart_attack_triggers_override(self):
        result = check_emergency_override("Heart attack symptoms")
        self.assertTrue(result["override"])

    def test_unconscious_triggers_override(self):
        result = check_emergency_override("Patient is unconscious")
        self.assertTrue(result["override"])

    def test_mild_symptoms_no_override(self):
        result = check_emergency_override("mild headache and fatigue")
        self.assertFalse(result["override"])

    def test_case_insensitive(self):
        result = check_emergency_override("CHEST PAIN")
        self.assertTrue(result["override"])


# ─────────────────────────────────────────────
# safe_infer_priority — fallback behaviour
# ─────────────────────────────────────────────
class SafeInferPriorityTests(TestCase):

    @patch("triagesync_backend.apps.triage.services.triage_service.infer_priority", side_effect=Exception("AI timeout"))
    @override_settings(TRIAGE_FALLBACK=CUSTOM_FALLBACK)
    def test_ai_exception_returns_fallback(self, mock_ai):
        result = safe_infer_priority("some symptoms")
        self.assertEqual(result["priority"], 3)
        self.assertEqual(result["urgency_score"], 50)

    @patch("triagesync_backend.apps.triage.services.triage_service.infer_priority", return_value={"bad": "data"})
    @override_settings(TRIAGE_FALLBACK=CUSTOM_FALLBACK)
    def test_invalid_ai_output_returns_fallback(self, mock_ai):
        result = safe_infer_priority("some symptoms")
        self.assertEqual(result["priority"], 3)

    @patch("triagesync_backend.apps.triage.services.triage_service.infer_priority", return_value={
        "priority": 1, "urgency_score": 95, "condition": "Cardiac Event"
    })
    def test_valid_ai_output_returned_as_is(self, mock_ai):
        result = safe_infer_priority("chest pain")
        self.assertEqual(result["urgency_score"], 95)
        self.assertEqual(result["condition"], "Cardiac Event")


# ─────────────────────────────────────────────
# process_triage
# ─────────────────────────────────────────────
class ProcessTriageTests(TestCase):

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_critical_score_gives_priority_1(self):
        result = process_triage({"urgency_score": 95, "condition": "Cardiac Event"})
        self.assertEqual(result["priority"], 1)
        self.assertTrue(result["is_critical"])

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_low_score_gives_priority_5(self):
        result = process_triage({"urgency_score": 10, "condition": "Minor"})
        self.assertEqual(result["priority"], 5)
        self.assertFalse(result["is_critical"])

    @override_settings(PRIORITY_THRESHOLDS=CUSTOM_THRESHOLDS)
    def test_missing_score_defaults_to_50(self):
        result = process_triage({"condition": "Unknown"})
        # score defaults to 50 → priority 3
        self.assertEqual(result["priority"], 3)


# ─────────────────────────────────────────────
# Critical alert broadcast
# ─────────────────────────────────────────────
class CriticalAlertBroadcastTests(TestCase):

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.check_emergency_override",
        return_value={
            "override": True,
            "urgency_score": 100,
            "condition": "Emergency Override",
            "category": "General",
            "explanation": ["Emergency keyword matched"],
            "recommended_action": "Immediate medical attention required",
            "reason": "Emergency override triggered.",
            "priority_level": 1,
            "is_critical": True,
            "source": "EMERGENCY_OVERRIDE"
        })
    def test_critical_alert_fired_for_priority_1(self, mock_override, mock_update, mock_alert):
        evaluate_triage("chest pain")
        mock_alert.assert_called_once()

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.safe_infer_priority",
        return_value={"priority": 4, "urgency_score": 30, "condition": "Minor"})
    def test_critical_alert_not_fired_for_low_priority(self, mock_ai, mock_update, mock_alert):
        evaluate_triage("mild headache")
        mock_alert.assert_not_called()


# ─────────────────────────────────────────────
# priority_update always fires
# ─────────────────────────────────────────────
class PriorityUpdateBroadcastTests(TestCase):

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.safe_infer_priority",
            return_value={"priority": 3, "urgency_score": 50, "condition": "Fever"})
    def test_priority_update_always_fired(self, mock_ai, mock_update, mock_alert):
        evaluate_triage("fever")
        mock_update.assert_called_once()


# ─────────────────────────────────────────────
# Full evaluate_triage integration
# ─────────────────────────────────────────────
class EvaluateTriageIntegrationTests(TestCase):

    def test_empty_symptoms_raises(self):
        with self.assertRaises(ValueError):
            evaluate_triage("")

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.check_emergency_override",
        return_value={
            "override": True,
            "urgency_score": 100,
            "condition": "Emergency Override",
            "category": "General",
            "explanation": ["Emergency keyword matched"],
            "recommended_action": "Immediate medical attention required",
            "reason": "Emergency override triggered.",
            "priority_level": 1,
            "is_critical": True,
            "source": "EMERGENCY_OVERRIDE"
        })
    def test_emergency_override_returns_priority_1(self, mock_override, mock_update, mock_alert):
        response = evaluate_triage("chest pain and sweating")
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["triage_result"]["priority"], 1)
        self.assertEqual(response["data"]["source"], "EMERGENCY_OVERRIDE")
        self.assertEqual(response["data"]["event"]["event_type"], "CRITICAL_ALERT")

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.safe_infer_priority",
           return_value={"priority": 3, "urgency_score": 50, "condition": "Fever"})
    def test_ai_path_returns_correct_structure(self, mock_ai, mock_update, mock_alert):
        response = evaluate_triage("mild fever")
        self.assertTrue(response["success"])
        data = response["data"]
        self.assertIn("triage_result", data)
        self.assertIn("event", data)
        self.assertEqual(data["source"], "AI_SYSTEM")
        self.assertEqual(data["module"], "member6_triage_service")

    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_critical_alert")
    @patch("triagesync_backend.apps.triage.services.triage_service.trigger_priority_update")
    @patch("triagesync_backend.apps.triage.services.triage_service.ai_service.infer_priority",
        return_value={"priority": 3, "urgency_score": 50, "condition": "Unknown"})
    def test_fallback_ai_output_used_on_failure(self, mock_ai, mock_update, mock_alert):
        response = evaluate_triage("some vague complaint")
        self.assertEqual(response["data"]["triage_result"]["urgency_score"], 50)
        self.assertEqual(response["data"]["triage_result"]["priority"], 3)
