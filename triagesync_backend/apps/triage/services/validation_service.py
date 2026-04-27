from django.conf import settings


# -------------------------
# Symptom input validation
# -------------------------
MAX_SYMPTOM_LENGTH = 500


def validate_symptoms(symptoms: str) -> str:
    """
    Validate and clean raw symptom input. Returns cleaned string.
    
    Raises:
        ValueError: If symptoms are empty, not a string, or exceed 500 characters.
    """
    if not isinstance(symptoms, str) or not symptoms.strip():
        raise ValueError("Symptoms are required.")
    
    cleaned = symptoms.strip()
    
    if len(cleaned) > MAX_SYMPTOM_LENGTH:
        raise ValueError(f"Symptoms cannot exceed {MAX_SYMPTOM_LENGTH} characters.")
    
    return cleaned


# -------------------------
# AI output validation + fallback
# -------------------------
REQUIRED_AI_KEYS = {"priority", "urgency_score", "condition"}


def validate_ai_output(ai_output: dict) -> bool:
    """Return True if ai_output contains all required keys with valid values."""
    if not isinstance(ai_output, dict):
        return False
    if not REQUIRED_AI_KEYS.issubset(ai_output.keys()):
        return False
    score = ai_output.get("urgency_score")
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        return False
    priority = ai_output.get("priority")
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        return False
    return True


def get_fallback_ai_output() -> dict:
    """Return safe fallback AI output when AI is unavailable or invalid."""
    fallback = getattr(settings, "TRIAGE_FALLBACK", {})
    return {
        "priority": fallback.get("priority", 3),
        "urgency_score": fallback.get("urgency_score", 50),
        "condition": fallback.get("condition", "Unknown"),
    }
