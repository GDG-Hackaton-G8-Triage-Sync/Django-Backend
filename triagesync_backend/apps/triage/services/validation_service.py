def validate_symptoms(symptoms: str) -> None:
    if not isinstance(symptoms, str) or not symptoms.strip():
        raise ValueError("Symptoms are required.")
