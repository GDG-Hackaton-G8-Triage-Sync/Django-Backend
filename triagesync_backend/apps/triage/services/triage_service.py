
"""
Triage Service — Member 6 (Triage Logic & Business Rules)

Responsibilities:
- Validate symptom input
- Run emergency keyword override check
- Call AI service and validate its output (with fallback)
- Calculate priority (1-5) using configurable thresholds
- Trigger critical_alert event for priority == 1
- Emit priority_update real-time event
- Return structured triage result
"""
from django.conf import settings

from .ai_service import infer_priority
from .ai_service import get_triage_recommendation
from . import ai_service
from .validation_service import get_fallback_ai_output, validate_ai_output, validate_symptoms
from .triage_config import PRIORITY_THRESHOLDS, TRIAGE_FALLBACK
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_critical_alert
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_priority_update
from triagesync_backend.apps.notifications.services.notification_service import NotificationService
from django.contrib.auth import get_user_model
import logging

from . import keyword_extraction


logger = logging.getLogger("triage.enrichment")

User = get_user_model()




# -------------------------
# Emergency keyword override
# -------------------------
EMERGENCY_KEYWORDS = [
    "chest pain",
    "no breathing",
    "not breathing",
    "unconscious",
    "unresponsive",
    "severe bleeding",
    "heart attack",
    "stroke",
    "seizure",
    "cardiac arrest",
]


def check_emergency_override(symptoms: str) -> dict:
    """
    Check if symptoms contain any life-threatening keywords.
    If so, bypass AI and return an immediate CRITICAL result.
    """
    text = symptoms.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text:
            # Ensure all contract fields are present for emergency override
            return {
                "override": True,
                "matched_keyword": keyword,
                "urgency_score": 100,
                "condition": "Emergency Override",
                "category": "General",
                "explanation": [f"Matched emergency keyword: {keyword}"],
                "recommended_action": "Immediate medical attention required",
                "reason": "Emergency override triggered.",
                "priority_level": 1,
                "is_critical": True,
                "source": "EMERGENCY_OVERRIDE"
            }
    # For non-emergency, still provide all contract fields with safe defaults
    return {
        "override": False,
        "condition": "Unknown",
        "urgency_score": 50,
        "category": "General",
        "explanation": ["No emergency keyword matched."],
        "recommended_action": "Staff review required",
        "reason": "No emergency override.",
        "priority_level": 5,
        "is_critical": False,
        "source": "AI_SYSTEM"
    }


# -------------------------
# Priority calculation
# -------------------------
def calculate_priority(urgency_score: int) -> int:
    """
    Map urgency score (0-100) to priority level (1-5).
    Thresholds are read from triage_config.PRIORITY_THRESHOLDS so they
    can be tuned without code changes.
    """
    thresholds = PRIORITY_THRESHOLDS

    if urgency_score >= thresholds["critical"]:
        return 1
    if urgency_score >= thresholds["high"]:
        return 2
    if urgency_score >= thresholds["medium"]:
        return 3
    if urgency_score >= thresholds["low"]:
        return 4
    return 5


# -------------------------
# AI call with fallback
# -------------------------
def safe_infer_priority(symptoms: str) -> dict:
    """
    Call AI service and validate its output.
    Prioritizes Gemini AI over legacy rule-based inference.
    """
    try:
        # 1. Legacy-first compatibility path used by existing tests/callers.
        legacy_ai = infer_priority(symptoms)
        if validate_ai_output(legacy_ai):
            legacy_ai.setdefault("source", "AI_SYSTEM")
            legacy_ai.setdefault("priority_level", legacy_ai.get("priority"))
            return legacy_ai

        # 2. Try the full AI recommendation (Gemini)
        ai_raw = get_triage_recommendation(symptoms)

        # If AI returned a valid recommendation (not an error envelope)
        if isinstance(ai_raw, dict) and not ai_raw.get("error"):
            ai_raw.setdefault("source", "GEMINI_AI")
            # Sync priority keys
            if "priority" not in ai_raw and "priority_level" in ai_raw:
                ai_raw["priority"] = ai_raw["priority_level"]
            elif "priority_level" not in ai_raw and "priority" in ai_raw:
                ai_raw["priority_level"] = ai_raw["priority"]
            return ai_raw

        # 3. Fallback to rule-based inference and then system fallback
        logger.info("[Triage] Gemini failed or returned error, falling back to rule-based inference")
        legacy_ai = infer_priority(symptoms)
        if validate_ai_output(legacy_ai):
            # Map legacy format to the richer M5 format
            return {
                "priority": legacy_ai.get("priority", 3),
                "priority_level": legacy_ai.get("priority", 3),
                "urgency_score": legacy_ai.get("urgency_score", 50),
                "condition": legacy_ai.get("condition", "Unknown"),
                "category": "General",
                "explanation": ["Rule-based fallback triggered"],
                "reason": "Analysis of symptom vectors indicates clinical correlation required.",
                "recommended_action": "Staff clinical review recommended.",
                "confidence": 0.0,
                "source": "RULE_ENGINE_FALLBACK",
                "is_critical": legacy_ai.get("urgency_score", 0) >= PRIORITY_THRESHOLDS["critical"]
            }

        fallback = get_fallback_ai_output()
        fallback["source"] = "SYSTEM_FALLBACK"
        fallback.setdefault("priority_level", fallback.get("priority", 3))
        return fallback
    except Exception as e:
        logger.error(f"[Triage] AI inference failed critically: {e}")
        fallback = get_fallback_ai_output()
        fallback["source"] = "ERROR_FALLBACK"
        fallback.setdefault("priority_level", fallback.get("priority", 3))
        return fallback


# -------------------------
# Real-time event helpers
# -------------------------
def trigger_critical_alert(urgency_score: int, condition: str) -> None:
    """Log critical alert information and notify relevant staff."""
    # Note: Critical alert WebSocket broadcast is handled by broadcast_patient_created()
    # in TriageSubmissionView after PatientSubmission is created with patient_id
    try:
        import logging
        logger = logging.getLogger("triage.critical")
        logger.warning(f"Critical condition detected: {condition} (urgency: {urgency_score})")
        
        # Notify all supervisors and doctors about critical cases
        supervisors_and_doctors = User.objects.filter(role__in=["supervisor", "doctor"])
        if supervisors_and_doctors.exists():
            NotificationService.create_bulk_notifications(
                users=supervisors_and_doctors,
                notification_type="critical_alert",
                title="Critical Patient Alert",
                message=f"Priority 1 patient detected: {condition} (Urgency: {urgency_score})",
                metadata={
                    "urgency_score": urgency_score,
                    "condition": condition,
                    "alert_type": "critical_triage"
                }
            )
    except Exception:
        # Never let logging failure block the triage response
        pass


def trigger_priority_update(priority: int, urgency_score: int, condition: str) -> None:
    """Broadcast a priority_update WebSocket event and notify relevant staff."""
    try:
        # Fix: broadcast_priority_update expects individual parameters, not a dict
        broadcast_priority_update(patient_id=0, priority=priority, urgency_score=urgency_score)
        
        # Notify staff based on priority level
        if priority <= 2:  # High and Critical priority
            # Notify all doctors and supervisors for high priority cases
            staff_to_notify = User.objects.filter(role__in=["doctor", "supervisor"])
            notification_type = "priority_update"
            title = f"Priority {priority} Patient Alert"
            message = f"High priority patient requires attention: {condition} (Priority: {priority})"
        elif priority == 3:  # Medium priority
            # Notify available nurses and doctors for medium priority
            staff_to_notify = User.objects.filter(role__in=["nurse", "doctor"])
            notification_type = "priority_update"
            title = f"Priority {priority} Patient"
            message = f"Medium priority patient: {condition} (Priority: {priority})"
        else:
            # For low priority (4-5), no notifications needed
            staff_to_notify = User.objects.none()
        
        if staff_to_notify.exists():
            NotificationService.create_bulk_notifications(
                users=staff_to_notify,
                notification_type=notification_type,
                title=title,
                message=message,
                metadata={
                    "priority": priority,
                    "urgency_score": urgency_score,
                    "condition": condition,
                    "alert_type": "priority_update"
                }
            )
    except Exception:
        pass


def build_event(priority: int, urgency_score: int) -> dict:
    """Build the inline event summary returned in the API response."""
    if priority == 1:
        return {
            "event_type": "CRITICAL_ALERT",
            "level": "HIGH",
            "message": "Immediate medical attention required",
        }
    if priority == 2:
        return {
            "event_type": "URGENT_ALERT",
            "level": "MEDIUM",
            "message": "Patient needs quick review",
        }
    return {
        "event_type": "LOG_ONLY",
        "level": "LOW",
        "message": "No immediate action required",
    }


# -------------------------
# Status management
# -------------------------
VALID_STATUSES = ["waiting", "in_progress", "completed"]


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validate status transition rules.
    Returns True if transition is allowed.
    """
    if new_status not in VALID_STATUSES:
        return False
    
    # Define allowed transitions
    allowed_transitions = {
        "waiting": ["in_progress", "completed"],
        "in_progress": ["completed", "waiting"],
        "completed": [],  # Cannot transition from completed
    }
    
    return new_status in allowed_transitions.get(current_status, [])


# -------------------------
# Core business rules
# -------------------------


def process_triage(ai_output, current_status="PENDING"):
    score = ai_output.get("urgency_score", 50)
    thresholds = PRIORITY_THRESHOLDS

    if score >= thresholds["critical"]:
        priority = 1
        status = "CRITICAL"
    elif score >= thresholds["high"]:
        priority = 2
        status = "URGENT"
    elif score >= thresholds["medium"]:
        priority = 3
        status = "MEDIUM"
    elif score >= thresholds["low"]:
        priority = 4
        status = "STABLE"
    else:
        priority = 5
        status = "STABLE"

    return {
        "priority": priority,
        "urgency_score": score,
        "status": status,
        "is_critical": score >= thresholds["critical"]
    }
# -------------------------
# Entry point
# -------------------------
def evaluate_triage(symptoms: str, current_status="PENDING"):
    # 1. Validate input
    clean_symptoms = validate_symptoms(symptoms)

    # 2. Check for emergency override
    override = check_emergency_override(clean_symptoms)
    ai_contract_fields = [
        "urgency_score", "condition", "category", "explanation", "recommended_action", 
        "reason", "priority_level", "is_critical", "source", "confidence"
    ]
    
    # Default values for all contract fields
    ai_contract_defaults = {
        "urgency_score": 50,
        "condition": "Unknown",
        "category": "General",
        "explanation": [],
        "recommended_action": "Staff review required",
        "reason": "No specific reason provided",
        "priority_level": 5,
        "is_critical": False,
        "source": "UNKNOWN",
        "confidence": 0.0
    }
    
    if override["override"]:
        ai_payload = override
    else:
        ai_payload = safe_infer_priority(clean_symptoms)

    # 4. Apply business rules (Member 6 logic)
    triage_result = process_triage(ai_payload, current_status)

    # Trigger real-time events
    trigger_priority_update(
        triage_result["priority"],
        triage_result["urgency_score"],
        ai_payload.get("condition", "Unknown")
    )
    if triage_result["is_critical"]:
        trigger_critical_alert(triage_result["urgency_score"], ai_payload.get("condition", "Unknown"))

    # 5. Build SYSTEM RESPONSE with guaranteed contract fields
    ai_contract = {}
    for field in ai_contract_fields:
        ai_contract[field] = ai_payload.get(field, ai_contract_defaults.get(field))
    
    response = {
        "success": True,
        "data": {
            "source": ai_payload.get("source", "UNKNOWN"),
            "module": "member6_triage_service",
            "triage_result": triage_result,
            "ai_contract": ai_contract,
            "staff_view": {
                "priority": triage_result["priority"],
                "status": triage_result["status"],
                "is_critical": triage_result["is_critical"]
            },
            "admin_view": {
                "urgency_score": ai_payload.get("urgency_score"),
                "decision_source": ai_payload.get("source", "AI + RULE_ENGINE")
            },
            "system_meta": {
                "status_flow": current_status,
                "source": "AI -> BRIDGE -> RULES"
            },
            "event": build_event(triage_result["priority"], triage_result["urgency_score"])
        }
    }

    return response


def enrich_triage_response(ai_response: dict, patient) -> dict:
    """Enrich AI triage response with extracted keywords, flags, and patient-derived info.

    Returns a dictionary with keys used by tests and the UI:
    - critical_keywords: list[str]
    - requires_immediate_attention: bool
    - specialist_referral_suggested: bool
    - has_allergies: bool
    - risk_factors: list[str]

    This function is defensive: on any exception it returns safe defaults and logs the error.
    """
    defaults = {
        "critical_keywords": [],
        "requires_immediate_attention": False,
        "specialist_referral_suggested": False,
        "has_allergies": False,
        "risk_factors": [],
    }

    try:
        explanation = ai_response.get("explanation") if isinstance(ai_response, dict) else None
        recommended_action = ai_response.get("recommended_action", "") if isinstance(ai_response, dict) else ""

        # Critical keywords from AI explanation (list of strings)
        critical_keywords = []
        if isinstance(explanation, list) and explanation:
            # Join explanation snippets for robust matching
            joined = " \n ".join([str(s) for s in explanation if isinstance(s, str)])
            critical_keywords = keyword_extraction.extract_keywords(joined, keyword_extraction.CRITICAL_KEYWORDS)
            if critical_keywords:
                logger.info(
                    "Critical keywords detected in AI explanation",
                    extra={"critical_keywords": critical_keywords, "keyword_count": len(critical_keywords)}
                )

        # Urgency detection from recommended_action
        ra_lower = recommended_action.lower() if isinstance(recommended_action, str) else ""
        requires_immediate = any(indicator in ra_lower for indicator in keyword_extraction.URGENCY_INDICATORS)
        if requires_immediate:
            logger.info("Immediate attention flag set", extra={"recommended_action": recommended_action})

        # Specialist referral detection
        specialist_referral = any(indicator in ra_lower for indicator in keyword_extraction.SPECIALIST_INDICATORS)
        if specialist_referral:
            logger.info("Specialist referral flag set", extra={"recommended_action": recommended_action})

        # Patient-derived flags
        has_allergies = False
        try:
            if patient and hasattr(patient, "allergies") and isinstance(patient.allergies, str):
                if patient.allergies.strip():
                    has_allergies = True
        except Exception:
            has_allergies = False

        # Risk factors from patient health_history
        risk_factors = []
        try:
            if patient and hasattr(patient, "health_history") and isinstance(patient.health_history, str):
                risk_factors = keyword_extraction.extract_keywords(patient.health_history, keyword_extraction.CHRONIC_CONDITIONS)
                if risk_factors:
                    logger.info("Risk factors detected", extra={"risk_factors": risk_factors})
        except Exception:
            risk_factors = []

        return {
            "critical_keywords": critical_keywords,
            "requires_immediate_attention": requires_immediate,
            "specialist_referral_suggested": specialist_referral,
            "has_allergies": has_allergies,
            "risk_factors": risk_factors,
        }
    except Exception:
        logger.error("Triage response enrichment failed", exc_info=True)
        return defaults
