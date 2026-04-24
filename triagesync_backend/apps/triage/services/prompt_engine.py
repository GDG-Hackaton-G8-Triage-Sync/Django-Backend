def build_triage_prompt(symptoms: str) -> str:
    return f"Assess urgency for symptoms: {symptoms.strip()}"