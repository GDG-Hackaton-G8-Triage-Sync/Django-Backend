"""
AI service — infers an urgency score (0-100) from symptom text.

Returns an integer score that maps to priority levels via PRIORITY_THRESHOLDS.
The output schema matches the API contract:
    {"priority": int, "urgency_score": int, "condition": str}
"""


# Keyword → (urgency_score, condition) mapping
_SYMPTOM_RULES = [
    (["chest pain", "heart attack", "cardiac"], 95, "Cardiac Event"),
    (["no breathing", "not breathing", "stopped breathing"], 95, "Respiratory Arrest"),
    (["unconscious", "unresponsive"], 90, "Loss of Consciousness"),
    (["severe bleeding", "heavy bleeding"], 88, "Severe Hemorrhage"),
    (["stroke", "facial droop", "slurred speech"], 92, "Stroke"),
    (["seizure", "convulsion"], 85, "Seizure"),
    (["high fever", "fever above 40", "fever above 39"], 70, "High Fever"),
    (["fever", "temperature"], 65, "Fever"),
    (["severe pain", "extreme pain"], 68, "Severe Pain"),
    (["dizzy", "dizziness", "lightheaded"], 55, "Dizziness"),
    (["pain", "ache", "aching"], 50, "Pain"),
    (["nausea", "vomiting"], 45, "Nausea/Vomiting"),
    (["cough", "cold", "runny nose"], 30, "Minor Respiratory"),
]


def infer_priority(symptoms: str) -> dict:
    """
    Analyse symptom text and return an AI output dict.

    Returns:
        {"priority": int, "urgency_score": int, "condition": str}
    """
    text = symptoms.lower()

    for keywords, score, condition in _SYMPTOM_RULES:
        if any(kw in text for kw in keywords):
            priority = _score_to_priority(score)
            return {
                "priority": priority,
                "urgency_score": score,
                "condition": condition,
            }

    # Default — low urgency
    return {
        "priority": 5,
        "urgency_score": 15,
        "condition": "General Complaint",
    }


def _score_to_priority(score: int) -> int:
    """Convert urgency score to priority level 1-5."""
    if score >= 80:
        return 1
    if score >= 60:
        return 2
    if score >= 40:
        return 3
    if score >= 20:
        return 4
    return 5
