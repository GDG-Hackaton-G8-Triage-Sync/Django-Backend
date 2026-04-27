
"""
Triage Service — Member 6 (Triage Logic & Business Rules)

Responsibilities:
- Validate symptom input
- Run emergency keyword override check
- Call AI service and validate its output (with fallback)
- Calculate priority (1-5) using configurable thresholds
- Trigger critical_alert event for priority == 1
- Emit priority_update real-time event
- Return structured triage result
"""
from django.conf import settings

from .ai_service import infer_priority
from .ai_service import get_triage_recommendation
from .validation_service import get_fallback_ai_output, validate_ai_output, validate_symptoms
from .triage_config import PRIORITY_THRESHOLDS, TRIAGE_FALLBACK
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_critical_alert
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_priority_update




# -------------------------
# Emergency keyword override
# -------------------------
EMERGENCY_KEYWORDS = [
    "chest pain",
    "no breathing",
    "not breathing",
    "unconscious",
    "unresponsive",
    "severe bleeding",
    "heart attack",
    "stroke",
    "seizure",
    "cardiac arrest",
]


def check_emergency_override(symptoms: str) -> dict:
    """
    Check if symptoms contain any life-threatening keywords.
    If so, bypass AI and return an immediate CRITICAL result.
    """
    text = symptoms.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text:
            # Ensure all contract fields are present for emergency override
            return {
                "override": True,
                "matched_keyword": keyword,
                "urgency_score": 100,
                "condition": "Emergency Override",
                "category": "General",
                "explanation": [f"Matched emergency keyword: {keyword}"],
                "recommended_action": "Immediate medical attention required",
                "reason": "Emergency override triggered.",
                "priority_level": 1,
                "is_critical": True,
                "source": "EMERGENCY_OVERRIDE"
            }
    # For non-emergency, still provide all contract fields with safe defaults
    return {
        "override": False,
        "condition": "Unknown",
        "urgency_score": 50,
        "category": "General",
        "explanation": ["No emergency keyword matched."],
        "recommended_action": "Staff review required",
        "reason": "No emergency override.",
        "priority_level": 5,
        "is_critical": False,
        "source": "AI_SYSTEM"
    }


# -------------------------
# Priority calculation
# -------------------------
def calculate_priority(urgency_score: int) -> int:
    """
    Map urgency score (0-100) to priority level (1-5).
    Thresholds are read from triage_config.PRIORITY_THRESHOLDS so they
    can be tuned without code changes.
    """
    thresholds = PRIORITY_THRESHOLDS

    if urgency_score >= thresholds["critical"]:
        return 1
    if urgency_score >= thresholds["high"]:
        return 2
    if urgency_score >= thresholds["medium"]:
        return 3
    if urgency_score >= thresholds["low"]:
        return 4
    return 5


# -------------------------
# AI call with fallback
# -------------------------
def safe_infer_priority(symptoms: str) -> dict:
    """
    Call AI service and validate its output.
    Falls back to default values if AI fails or returns invalid data.
    """
    try:
        ai_output = infer_priority(symptoms)
        if validate_ai_output(ai_output):
            return ai_output
        # AI returned something but it's malformed — use fallback
        return get_fallback_ai_output()
    except Exception:
        return get_fallback_ai_output()


# -------------------------
# Real-time event helpers
# -------------------------
def trigger_critical_alert(urgency_score: int, condition: str) -> None:
    """Broadcast a critical_alert WebSocket event (priority == 1)."""
    try:
        broadcast_critical_alert({
            "urgency_score": urgency_score,
            "condition": condition,
            "message": "Immediate medical attention required",
        })
    except Exception:
        # Never let broadcast failure block the triage response
        pass


def trigger_priority_update(priority: int, urgency_score: int, condition: str) -> None:
    """Broadcast a priority_update WebSocket event whenever priority is set."""
    try:
        broadcast_priority_update({
            "priority": priority,
            "urgency_score": urgency_score,
            "condition": condition,
        })
    except Exception:
        pass


def build_event(priority: int, urgency_score: int) -> dict:
    """Build the inline event summary returned in the API response."""
    if priority == 1:
        return {
            "event_type": "critical_alert",
            "level": "HIGH",
            "message": "Immediate medical attention required",
        }
    if priority == 2:
        return {
            "event_type": "urgent_alert",
            "level": "MEDIUM",
            "message": "Patient needs quick review",
        }
    return {
        "event_type": "log_only",
        "level": "LOW",
        "message": "No immediate action required",
    }


# -------------------------
# Core business rules
# -------------------------


def process_triage(ai_output, current_status="PENDING"):
    score = ai_output.get("urgency_score", 50)
    thresholds = PRIORITY_THRESHOLDS

    if score >= thresholds["critical"]:
        priority = 1
        status = "CRITICAL"
    elif score >= thresholds["high"]:
        priority = 2
        status = "URGENT"
    elif score >= thresholds["medium"]:
        priority = 3
        status = "MEDIUM"
    elif score >= thresholds["low"]:
        priority = 4
        status = "STABLE"
    else:
        priority = 5
        status = "STABLE"

    return {
        "priority": priority,
        "urgency_score": score,
        "status": status,
        "is_critical": score >= thresholds["critical"]
    }
# -------------------------
# Entry point
# -------------------------
def evaluate_triage(symptoms: str, current_status="PENDING"):
    # 1. Validate input
    clean_symptoms = validate_symptoms(symptoms)

    # 2. Check for emergency override
    override = check_emergency_override(clean_symptoms)
    ai_contract_fields = [
        "urgency_score", "condition", "category", "explanation", "recommended_action", "reason", "priority_level", "is_critical", "source"
    ]
    if override["override"]:
        ai_payload = override
        urgency_score = ai_payload["urgency_score"]
        condition = ai_payload["condition"]
        source = ai_payload["source"]
    else:
        ai_output = infer_priority(clean_symptoms)
        # Ensure ai_output is a dictionary with the expected keys
        if isinstance(ai_output, dict):
            urgency_score = ai_output.get("urgency_score", 50)
            condition = ai_output.get("condition", "Unknown")
            ai_payload = {field: ai_output.get(field, None) for field in ai_contract_fields}
            ai_payload["urgency_score"] = urgency_score
            ai_payload["condition"] = condition
            ai_payload["source"] = ai_output.get("source", "AI_SYSTEM")
            # Fill missing contract fields with safe defaults
            for field in ai_contract_fields:
                if ai_payload[field] is None:
                    if field == "category":
                        ai_payload[field] = "General"
                    elif field == "explanation":
                        ai_payload[field] = ["AI output missing explanation"]
                    elif field == "recommended_action":
                        ai_payload[field] = "Staff review required"
                    elif field == "reason":
                        ai_payload[field] = "AI output missing reason."
                    elif field == "priority_level":
                        ai_payload[field] = 5
                    elif field == "is_critical":
                        ai_payload[field] = False
                    elif field == "source":
                        ai_payload[field] = "AI_SYSTEM"
        else:
            urgency_score = 50
            condition = "Unknown"
            ai_payload = {
                "urgency_score": urgency_score,
                "condition": condition,
                "category": "General",
                "explanation": ["AI output missing or invalid"],
                "recommended_action": "Staff review required",
                "reason": "AI output missing or invalid.",
                "priority_level": 5,
                "is_critical": False,
                "source": "AI_SYSTEM"
            }
        source = ai_payload.get("source", "AI_SYSTEM")

    # 4. Apply business rules (Member 6 logic)
    triage_result = process_triage(ai_payload, current_status)

    # Trigger real-time events
    trigger_priority_update(
        triage_result["priority"],
        triage_result["urgency_score"],
        condition
    )
    if triage_result["is_critical"]:
        trigger_critical_alert(triage_result["urgency_score"], condition)

    # 5. Build SYSTEM RESPONSE (THIS IS YOUR KEY ROLE)
    response = {
        "success": True,
        "data": {
            "source": source,
            "module": "member6_triage_service",
            "triage_result": triage_result,
            "ai_contract": {field: ai_payload.get(field) for field in ai_contract_fields if field in ai_payload},
            "staff_view": {
                "priority": triage_result["priority"],
                "status": triage_result["status"],
                "is_critical": triage_result["is_critical"]
            },
            "admin_view": {
                "urgency_score": urgency_score,
                "decision_source": "AI + RULE_ENGINE"
            },
            "system_meta": {
                "status_flow": current_status,
                "source": "AI -> BRIDGE -> RULES"
            },
            "event": build_event(triage_result["priority"], triage_result["urgency_score"])
        }
    }

    return response
