from .ai_service import infer_priority
from .validation_service import validate_symptoms , datetime


# -------------------------
# Fallback AI safety
# -------------------------
def safe_infer_priority(symptoms):
    try:
        return infer_priority(symptoms)
    except Exception:
        return 40


# -------------------------
# Status lifecycle logic
# -------------------------
def update_status(current_status, score):
    if current_status == "PENDING":
        return "TRIAGED"

    if score >= 80:
        return "ESCALATED"

    if score < 40:
        return "STABLE"

    return current_status


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
# Entry function (ONLY ONE)
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