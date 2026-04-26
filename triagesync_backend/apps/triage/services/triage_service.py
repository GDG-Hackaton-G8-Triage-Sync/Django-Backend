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
from .validation_service import get_fallback_ai_output, validate_ai_output, validate_symptoms
from apps.realtime.services.broadcast_service import broadcast_critical_alert
from apps.realtime.services.broadcast_service import broadcast_priority_update

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
            return {
                "override": True,
                "matched_keyword": keyword,
                "urgency_score": 100,
                "condition": "Emergency Override",
            }
    return {"override": False}


# -------------------------
# Priority calculation
# -------------------------
def calculate_priority(urgency_score: int) -> int:
    """
    Map urgency score (0-100) to priority level (1-5).
    Thresholds are read from settings.PRIORITY_THRESHOLDS so they
    can be tuned without code changes.
    """
    thresholds = getattr(settings, "PRIORITY_THRESHOLDS", {
        "critical": 80,
        "high": 60,
        "medium": 40,
        "low": 20,
    })

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
from .ai_service import infer_priority
from .validation_service import validate_symptoms


def process_triage(ai_output, current_status="PENDING"):
    score = ai_output.get("urgency_score", 0)

    if score >= 80:
        priority = 1
        status = "CRITICAL"
    elif score >= 60:
        priority = 2
        status = "URGENT"
    elif score >= 40:
        priority = 3
        status = "MEDIUM"
    else:
        priority = 4
        status = "STABLE"

    return {
        "priority": priority,
        "urgency_score": score,
        "status": status,
        "is_critical": score >= 80
    }
# -------------------------
# Entry point
# -------------------------
def evaluate_triage(symptoms: str, current_status="PENDING"):
    # 1. Validate input
    clean_symptoms = validate_symptoms(symptoms)

    # 2. AI layer (Member 5)
    ai_score = infer_priority(clean_symptoms)

    # 3. Normalize AI output (BRIDGE STEP - YOUR ROLE)
    ai_payload = {
        "ai_score": ai_score,
        "urgency_score": ai_score * 20,
        "source": "AI_SERVICE"
    }

    # 4. Apply business rules (Member 6 logic)
    triage_result = process_triage(ai_payload, current_status)

    # 5. Build SYSTEM RESPONSE (THIS IS YOUR KEY ROLE)
    response = {
        "triage_result": triage_result,

        # 👇 for staff dashboard
        "staff_view": {
            "priority": triage_result["priority"],
            "status": triage_result["status"],
            "is_critical": triage_result["is_critical"]
        },

        # 👇 for admin dashboard
        "admin_view": {
            "ai_score": ai_score,
            "urgency_score": ai_payload["urgency_score"],
            "decision_source": "AI + RULE_ENGINE"
        },

        # 👇 for system tracking
        "system_meta": {
            "module": "member6_bridge",
            "status_flow": current_status,
            "source": "AI -> BRIDGE -> RULES"
        }
    }

    return response
def trigger_event(result):
    status = result.get("status")
    score = result.get("urgency_score")

    if status == "CRITICAL" or score >= 80:
        return {
            "event_type": "EMERGENCY_ALERT",
            "level": "HIGH",
            "message": "Immediate medical attention required"
        }

    if status == "URGENT":
        return {
            "event_type": "URGENT_ALERT",
            "level": "MEDIUM",
            "message": "Patient needs quick review"
        }

    return {
        "event_type": "LOG_ONLY",
        "level": "LOW",
        "message": "No immediate action required"
    }

EMERGENCY_KEYWORDS = [
    "chest pain",
    "no breathing",
    "unconscious",
    "severe bleeding",
    "heart attack",
    "stroke"
]

def check_emergency_override(symptoms: str):
    text = symptoms.lower()

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text:
            return {
                "override": True,
                "urgency_score": 100,
                "status": "CRITICAL"
            }

    return {"override": False}