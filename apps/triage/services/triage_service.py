from .ai_service import infer_priority
from .validation_service import validate_symptoms


def evaluate_triage(symptoms: str):
    validate_symptoms(symptoms)
    priority = infer_priority(symptoms)
    return {
        "priority": priority,
        "explanation": f"Assigned {priority} priority based on submitted symptoms.",
    }
