def infer_priority(symptoms: str) -> str:
    text = symptoms.lower()
    if any(keyword in text for keyword in ["chest pain", "unconscious", "stroke"]):
        return "high"
    if any(keyword in text for keyword in ["fever", "pain", "dizzy"]):
        return "medium"
    return "low"
