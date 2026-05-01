"""
Demographic extraction service using AI to extract age, gender, and blood_type
from symptom text.

This service uses Gemini AI to intelligently extract demographic information
that may be mentioned in the symptoms description, enabling more accurate
triage without requiring explicit demographic fields.
"""
import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger("triage.demographics")

# Ensure GEMINI_API_KEY is set
if not os.environ.get("GEMINI_API_KEY"):
    try:
        from django.conf import settings
        os.environ["GEMINI_API_KEY"] = getattr(settings, "GEMINI_API_KEY", "")
    except ImportError:
        pass


def extract_demographics_from_text(text: str) -> dict:
    """
    Extract age, gender, and blood_type from symptom text using AI.
    
    Args:
        text: The symptoms or medical text to analyze
        
    Returns:
        dict with keys:
            - age: int or None
            - gender: str (male/female/other) or None
            - blood_type: str (A+, O-, etc.) or None
            - confidence: str (high/medium/low) - overall confidence
            
    Example:
        >>> extract_demographics_from_text("45 year old male with chest pain")
        {'age': 45, 'gender': 'male', 'blood_type': None, 'confidence': 'high'}
    """
    if not text or not text.strip():
        return {'age': None, 'gender': None, 'blood_type': None, 'confidence': 'low'}
    
    prompt = _build_extraction_prompt(text)
    
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        # Normalize the extracted data
        normalized = {
            'age': _normalize_extracted_age(result.get('age')),
            'gender': _normalize_extracted_gender(result.get('gender')),
            'blood_type': _normalize_extracted_blood_type(result.get('blood_type')),
            'confidence': result.get('confidence', 'low')
        }
        
        logger.info(
            "[Demographics] Extracted from text: age=%s, gender=%s, blood_type=%s, confidence=%s",
            normalized['age'], normalized['gender'], normalized['blood_type'], normalized['confidence']
        )
        
        return normalized
        
    except Exception as e:
        logger.error("[Demographics] Extraction failed: %s", str(e))
        return {'age': None, 'gender': None, 'blood_type': None, 'confidence': 'low'}


def _build_extraction_prompt(text: str) -> str:
    """Build the AI prompt for demographic extraction."""
    return f"""Extract demographic information from the following medical text.

Text: "{text}"

Extract ONLY information that is explicitly mentioned or strongly implied in the text.
Do NOT make assumptions or infer information that is not clearly stated.

Return a JSON object with these fields:
- age: integer age if mentioned (e.g., "45 year old" → 45), or null if not mentioned
- gender: "male", "female", "other", or null if not mentioned
- blood_type: blood type if mentioned (e.g., "A+", "O-", "AB+"), or null if not mentioned
- confidence: "high" if explicitly stated, "medium" if implied, "low" if uncertain

Examples:
- "45 year old male with chest pain" → {{"age": 45, "gender": "male", "blood_type": null, "confidence": "high"}}
- "Patient is a woman, blood type A positive" → {{"age": null, "gender": "female", "blood_type": "A+", "confidence": "high"}}
- "Elderly patient with fever" → {{"age": null, "gender": null, "blood_type": null, "confidence": "low"}}
- "Man in his 40s" → {{"age": 45, "gender": "male", "blood_type": null, "confidence": "medium"}}

Return JSON only, no explanation."""


def _normalize_extracted_age(age) -> int | None:
    """Normalize extracted age to valid integer or None."""
    if age is None:
        return None
    try:
        n = int(age)
        if 0 <= n <= 150:
            return n
    except (TypeError, ValueError):
        pass
    return None


def _normalize_extracted_gender(gender) -> str | None:
    """Normalize extracted gender to standard format."""
    if not gender:
        return None
    
    gender_map = {
        "male": "male", "m": "male", "man": "male", "boy": "male",
        "female": "female", "f": "female", "woman": "female", "girl": "female",
        "other": "other", "nonbinary": "other", "non-binary": "other",
    }
    
    normalized = str(gender).strip().lower()
    return gender_map.get(normalized, "other" if normalized else None)


def _normalize_extracted_blood_type(blood_type) -> str | None:
    """Normalize extracted blood type to standard format."""
    if not blood_type:
        return None
    
    blood_type_map = {
        "a+": "A+", "a positive": "A+", "a pos": "A+",
        "a-": "A-", "a negative": "A-", "a neg": "A-",
        "b+": "B+", "b positive": "B+", "b pos": "B+",
        "b-": "B-", "b negative": "B-", "b neg": "B-",
        "ab+": "AB+", "ab positive": "AB+", "ab pos": "AB+",
        "ab-": "AB-", "ab negative": "AB-", "ab neg": "AB-",
        "o+": "O+", "o positive": "O+", "o pos": "O+",
        "o-": "O-", "o negative": "O-", "o neg": "O-",
    }
    
    normalized = str(blood_type).strip().lower()
    return blood_type_map.get(normalized, None)


def detect_conflicts(ai_extracted: dict, profile_data: dict) -> dict:
    """
    Detect conflicts between AI-extracted demographics and profile data.
    
    Args:
        ai_extracted: dict with age, gender, blood_type from AI
        profile_data: dict with age, gender, blood_type from user profile
        
    Returns:
        dict with:
            - has_conflict: bool
            - conflicts: list of field names that conflict
            - ai_values: dict of AI-extracted values for conflicting fields
            - profile_values: dict of profile values for conflicting fields
    """
    conflicts = []
    ai_values = {}
    profile_values = {}
    
    for field in ['age', 'gender', 'blood_type']:
        ai_val = ai_extracted.get(field)
        profile_val = profile_data.get(field)
        
        # Only consider it a conflict if both values exist and differ
        if ai_val is not None and profile_val is not None and ai_val != profile_val:
            conflicts.append(field)
            ai_values[field] = ai_val
            profile_values[field] = profile_val
    
    return {
        'has_conflict': len(conflicts) > 0,
        'conflicts': conflicts,
        'ai_values': ai_values,
        'profile_values': profile_values
    }
