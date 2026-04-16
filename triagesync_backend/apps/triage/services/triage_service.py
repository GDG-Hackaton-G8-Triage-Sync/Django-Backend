from .ai_service import infer_priority
from .validation_service import validate_symptoms
from apps.realtime.services.broadcast_service import broadcast_patient_created


def process_triage(ai_output):
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


def evaluate_triage(symptoms: str):
    validate_symptoms(symptoms)

    priority = infer_priority(symptoms)

    ai_output = {
        "urgency_score": priority * 20,   # simple conversion
        "condition": "AI Generated"
    }

    final_result = process_triage(ai_output)

    return {
        "ai_priority": priority,
        "final_result": final_result
    }