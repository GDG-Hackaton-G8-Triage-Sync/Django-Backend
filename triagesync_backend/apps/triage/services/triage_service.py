from .ai_service import infer_priority
from .validation_service import validate_symptoms


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
def process_triage(ai_output, current_status="PENDING"):
    score = ai_output.get("urgency_score", 0)

    if score >= 80:
        priority = 1
        base_status = "CRITICAL"
    elif score >= 60:
        priority = 2
        base_status = "URGENT"
    elif score >= 40:
        priority = 3
        base_status = "MEDIUM"
    else:
        priority = 4
        base_status = "STABLE"

    # lifecycle override
    status = update_status(current_status, score)

    return {
        "priority": priority,
        "urgency_score": score,
        "status": status,
        "base_status": base_status,
        "is_critical": score >= 80
    }


# -------------------------
# Entry function (ONLY ONE)
# -------------------------
def evaluate_triage(symptoms: str, current_status="PENDING"):
    clean_symptoms = validate_symptoms(symptoms)

    # emergency override FIRST
    emergency = check_emergency_override(clean_symptoms)

    if emergency["override"]:
        result = {
            "priority": 1,
            "urgency_score": 100,
            "status": "CRITICAL",
            "is_critical": True
        }

        event = trigger_event(result)

        return {
            "triage_result": result,
            "event": event,
            "source": "EMERGENCY_OVERRIDE"
        }

    # normal flow
    score = safe_infer_priority(clean_symptoms)

    ai_output = {
        "urgency_score": score,
        "condition": "AI Generated"
    }

    result = process_triage(ai_output, current_status)

    event = trigger_event(result)

    return {
        "triage_result": result,
        "event": event,
        "source": "AI_SYSTEM"
    }

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