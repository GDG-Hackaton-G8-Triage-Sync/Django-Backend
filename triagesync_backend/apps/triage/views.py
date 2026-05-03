import re as _re
import json

# New AI-based triage endpoint
from .services.ai_service import get_triage_recommendation
from .serializers import TriageAIResponseSerializer
from .serializers import PDFUploadSerializer
from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
import logging
from django.core.exceptions import ValidationError

from .serializers import TriageAIResponseSerializer
from .services.prompt_engine import build_pdf_triage_prompt
from .services.ai_service import (
    call_gemini_api,
    normalize_ai_response,
    normalize_age,
    normalize_gender,
    normalize_blood_type,
)
from PyPDF2 import PdfReader

from .services.triage_service import evaluate_triage
# from .serializers import TriageInputSerializer  # Removed: does not exist
from triagesync_backend.apps.authentication.permissions import IsDoctor, IsPatient
from triagesync_backend.apps.core.response import success_response, error_response
from triagesync_backend.apps.core.validators import validate_description_length

# Required imports for TriageSubmissionView
from triagesync_backend.apps.patients.models import PatientSubmission, Patient
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_patient_created
from triagesync_backend.apps.notifications.services.notification_service import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()
MAX_INPUT_LENGTH = 500


def _json_safe_value(value):
    if hasattr(value, "name"):
        return getattr(value, "name", str(value))
    if isinstance(value, dict):
        return {key: _json_safe_value(inner_value) for key, inner_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    return value


def _persist_ai_submission(request, symptoms, ai_output, source, extra_metadata=None, photo_name=None):
    """Persist AI/PDF triage interactions as permanent submissions for authenticated patients."""
    user = request.user if request.user and request.user.is_authenticated else None
    if not user or getattr(user, "role", None) != "patient":
        return None

    try:
        patient = getattr(user, "patient_profile", None)
        if patient is None:
            patient = Patient.objects.filter(user=user).first()
        if patient is None:
            patient = Patient.objects.create(user=user, name=user.username)

        submitted_inputs = {
            key: _json_safe_value(request.data.get(key))
            for key in getattr(request.data, "keys", lambda: [])()
        }

        metadata = {
            "submitted_inputs": submitted_inputs,
            "ai_snapshot": _json_safe_value(ai_output),
            "source": source,
        }
        if extra_metadata:
            metadata.update(_json_safe_value(extra_metadata))

        return PatientSubmission.objects.create(
            patient=patient,
            symptoms=symptoms,
            photo_name=photo_name,
            priority=ai_output.get("priority_level"),
            urgency_score=ai_output.get("urgency_score"),
            condition=ai_output.get("condition"),
            category=ai_output.get("category"),
            is_critical=bool(ai_output.get("is_critical", False)),
            explanation=ai_output.get("explanation", []),
            recommended_action=ai_output.get("recommended_action"),
            reason=ai_output.get("reason"),
            confidence=ai_output.get("confidence"),
            source=source,
            requires_immediate_attention=bool(ai_output.get("requires_immediate_attention", False)),
            specialist_referral_suggested=bool(ai_output.get("specialist_referral_suggested", False)),
            critical_keywords=ai_output.get("critical_keywords", []),
            metadata=metadata,
        )
    except Exception as exc:
        logger = logging.getLogger("triage.persistence")
        logger.warning("Failed to persist AI triage submission: %s", exc)
        return None


def is_relevant(text):
    if not text or not isinstance(text, str):
        return False
    keywords = [
        "pain", "fever", "cough", "fracture", "bleeding", "shortness of breath", "dizzy", "vomiting", "rash", "injury", "trauma", "stroke", "cardiac", "chest", "headache", "infection", "wound", "burn", "swelling", "seizure", "unconscious", "weakness", "nausea", "diarrhea", "palpitation", "collapse"
    ]
    text_lower = text.lower()
    return any(_re.search(r"\b" + _re.escape(kw) + r"\b", text_lower) for kw in keywords)


class TriageAIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .services.demographic_extractor import extract_demographics_from_text, detect_conflicts

        warning = None
        error = getattr(request, "_triage_error", None)
        data = request.data
        symptoms = data.get("symptoms")
        age = data.get("age")
        gender = data.get("gender")
        blood_type = data.get("blood_type")

        ai_extracted = extract_demographics_from_text(symptoms) if symptoms else {
            "age": None, "gender": None, "blood_type": None, "confidence": "low"
        }

        profile_data = {"age": None, "gender": None, "blood_type": None}
        patient_context = None
        user = request.user if request.user and request.user.is_authenticated else None
        if user:
            # Prefer the OneToOne `patient_profile` relation when present (consistent with other views)
            patient = getattr(user, "patient_profile", None)
            if patient is None:
                try:
                    patient = Patient.objects.filter(user=user).first()
                except Exception:
                    patient = None

            if patient:
                profile_data["age"] = getattr(patient, "age", None)
                profile_data["gender"] = getattr(patient, "gender", None)
                profile_data["blood_type"] = getattr(patient, "blood_type", None)
                patient_context = {
                    "name": getattr(patient, "name", None),
                    "age": profile_data["age"],
                    "gender": profile_data["gender"],
                    "blood_type": profile_data["blood_type"],
                    "date_of_birth": getattr(patient, "date_of_birth", None),
                    "health_history": getattr(patient, "health_history", None),
                    "allergies": getattr(patient, "allergies", None),
                    "current_medications": getattr(patient, "current_medications", None),
                    "bad_habits": getattr(patient, "bad_habits", None),
                }

            # Normalize any profile-provided demographics early so fallback logic uses canonical values
            try:
                profile_data["age"] = normalize_age(profile_data.get("age"))
            except Exception:
                profile_data["age"] = None
            try:
                profile_data["gender"] = normalize_gender(profile_data.get("gender"))
            except Exception:
                profile_data["gender"] = None
            try:
                profile_data["blood_type"] = normalize_blood_type(profile_data.get("blood_type"))
            except Exception:
                profile_data["blood_type"] = None

        if not age and not gender and not blood_type:
            conflict_info = detect_conflicts(ai_extracted, profile_data)
            if conflict_info["has_conflict"]:
                return Response({
                    "error": "demographic_conflict",
                    "message": "We found conflicting demographic information. Please clarify which values are correct.",
                    "conflicts": conflict_info["conflicts"],
                    "ai_extracted": conflict_info["ai_values"],
                    "profile_data": conflict_info["profile_values"],
                    "instructions": "Please provide the correct values in your next request using the age, gender, or blood_type fields."
                }, status=status.HTTP_409_CONFLICT)

        if not age:
            age = ai_extracted.get("age") or profile_data.get("age")
        if not gender:
            gender = ai_extracted.get("gender") or profile_data.get("gender")
        if not blood_type:
            blood_type = ai_extracted.get("blood_type") or profile_data.get("blood_type")

        try:
            age = normalize_age(age)
        except Exception:
            age = None
        try:
            gender = normalize_gender(gender)
        except Exception:
            gender = None
        try:
            blood_type = normalize_blood_type(blood_type)
        except Exception:
            blood_type = None

        warnings = []
        if age in (None, ""):
            warnings.append("age_missing")
        if gender in (None, ""):
            warnings.append("gender_missing")
        if blood_type in (None, ""):
            warnings.append("blood_type_missing")

        if error:
            return Response({
                "error": "Missing symptoms.",
                "message": "Please provide at least one symptom to proceed."
            }, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(symptoms, str) and len(symptoms) > MAX_INPUT_LENGTH:
            return Response({
                "error": "Symptoms too long.",
                "message": f"Please limit your input to {MAX_INPUT_LENGTH} characters for best results."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not is_relevant(symptoms):
            return Response({
                "error": "Input not relevant.",
                "message": "Please provide symptoms or information related to a medical triage situation."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger = logging.getLogger("triage.ai")
            # Emit diagnostics to help tests verify fallback behavior
            logger.warning("TriageAIView: profile_data=%s", profile_data)
            logger.warning("TriageAIView: demographics before call: age=%s gender=%s blood_type=%s", age, gender, blood_type)
            logger.warning("TriageAIView: patient_context=%s", patient_context)

            try:
                result = get_triage_recommendation(
                    symptoms,
                    age=age,
                    gender=gender,
                    blood_type=blood_type,
                    patient_context=patient_context,
                )
            except TypeError as exc:
                # Backwards-compatibility: try progressively simpler signatures.
                msg = str(exc)
                # If only `patient_context` isn't accepted, try keeping blood_type.
                if "patient_context" in msg:
                    try:
                        result = get_triage_recommendation(symptoms, age=age, gender=gender, blood_type=blood_type)
                    except TypeError:
                        result = get_triage_recommendation(symptoms, age=age, gender=gender)
                elif "blood_type" in msg or "unexpected keyword argument" in msg:
                    # Older implementations may not accept blood_type; fall back without it.
                    result = get_triage_recommendation(symptoms, age=age, gender=gender)
                else:
                    raise
        except Exception as e:
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

        if isinstance(result, dict) and result.get("error"):
            logger = logging.getLogger("triage.ai")
            logger.warning("AI unavailable. details=%s", result.get("details"))
            return Response({
                "error": "AI unavailable, staff review required",
                "message": "Our AI triage service is temporarily unavailable. Your case will be queued for staff review.",
                "details": result.get("details", []),
                "error_types": result.get("error_types", []),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            response_data = dict(serializer.data)
            response_data["source"] = "ai"
            if warnings:
                response_data["warning"] = warnings

            enriched_output = dict(result)
            enriched_output["source"] = "ai"
            if warnings:
                enriched_output["warning"] = warnings
            _persist_ai_submission(
                request=request,
                symptoms=symptoms,
                ai_output=enriched_output,
                source="AI_ENDPOINT",
                extra_metadata={
                    "triage_inputs": {
                        "age": age,
                        "gender": gender,
                        "blood_type": blood_type,
                    }
                },
            )

            return Response(response_data)

        logger = logging.getLogger("triage.ai")
        logger.warning("AI response validation failed. errors=%s", serializer.errors)
        return Response({
            "error": "AI response format error.",
            "message": "AI response did not match expected format.",
            "details": serializer.errors,
            "raw_ai": result,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TriagePDFExtractView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        import logging
        from .services.demographic_extractor import extract_demographics_from_text, detect_conflicts

        logger = logging.getLogger("triage.pdf")
        symptoms_prompt = request.data.get("symptoms", "").strip()

        serializer = PDFUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("PDF upload: invalid serializer input: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = serializer.validated_data["file"]
        if not pdf_file or getattr(pdf_file, "size", None) == 0:
            logger.warning("PDF upload: empty file uploaded.")
            return Response({
                "error": "Empty file.",
                "message": "The uploaded file is empty. Please upload a valid PDF document."
            }, status=status.HTTP_400_BAD_REQUEST)
        if not getattr(pdf_file, "name", "").lower().endswith(".pdf"):
            logger.warning("PDF upload: non-PDF file uploaded: %s", getattr(pdf_file, "name", ""))
            return Response({
                "error": "Only PDF files are allowed.",
                "message": "Please upload a file with a .pdf extension."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            reader = PdfReader(pdf_file)
            pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            logger.warning("PDF extraction failed: %s", str(e))
            return Response({
                "error": "PDF extraction failed.",
                "message": "Could not extract text from the PDF. Please ensure the file is a valid, non-corrupted PDF.",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        max_text_length = 10000
        if len(pdf_text) > max_text_length:
            pdf_text = pdf_text[:max_text_length]

        if not pdf_text or not pdf_text.strip():
            logger.warning("PDF upload: no extractable text found.")
            return Response({
                "error": "No text extracted.",
                "message": "No extractable text found in the PDF. Please upload a PDF with selectable text."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not symptoms_prompt:
            logger.warning("PDF upload: missing symptoms prompt.")
            return Response({
                "error": "Missing symptoms prompt.",
                "message": "Please enter your current feeling, symptom, or pain along with the PDF so the triage AI can compare them.",
                "instructions": "Include a 'symptoms' field in your request with at least one symptom or feeling description."
            }, status=status.HTTP_400_BAD_REQUEST)

        if symptoms_prompt and not is_relevant(symptoms_prompt):
            logger.warning("PDF upload: symptoms prompt not relevant.")
            return Response({
                "error": "Symptoms not relevant.",
                "message": "The symptoms description does not appear to be related to a medical triage situation. Please provide relevant medical symptoms."
            }, status=status.HTTP_400_BAD_REQUEST)

        pdf_age = normalize_age(request.data.get("age"))
        pdf_gender = normalize_gender(request.data.get("gender"))
        pdf_blood_type = request.data.get("blood_type")

        user = request.user if request.user and request.user.is_authenticated else None
        if user and hasattr(user, "patient_profile"):
            patient = user.patient_profile
            if pdf_age is None and getattr(patient, "age", None) is not None:
                pdf_age = patient.age
            if not pdf_gender and getattr(patient, "gender", None):
                pdf_gender = patient.gender
            if not pdf_blood_type and getattr(patient, "blood_type", None):
                pdf_blood_type = patient.blood_type

        explicit_demographics_provided = any(
            value not in (None, "", []) for value in (request.data.get("age"), request.data.get("gender"), request.data.get("blood_type"))
        )

        prompt_demographics = extract_demographics_from_text(symptoms_prompt) if symptoms_prompt else {
            "age": None,
            "gender": None,
            "blood_type": None,
            "confidence": "low",
        }
        pdf_demographics = extract_demographics_from_text(pdf_text)

        if not explicit_demographics_provided:
            conflict_info = detect_conflicts(prompt_demographics, pdf_demographics)
            if conflict_info["has_conflict"]:
                return Response({
                    "error": "demographic_conflict",
                    "message": "We found conflicting demographic information between the text prompt and the uploaded PDF. Please confirm the correct values.",
                    "conflicts": conflict_info["conflicts"],
                    "prompt_values": conflict_info["ai_values"],
                    "pdf_values": conflict_info["profile_values"],
                    "instructions": "Please resend the request with the correct age, gender, or blood_type fields filled in. The confirmed values will be attached to the prompt on retry.",
                }, status=status.HTTP_409_CONFLICT)

        if pdf_age is None:
            pdf_age = prompt_demographics.get("age") or pdf_demographics.get("age")
        if not pdf_gender:
            pdf_gender = prompt_demographics.get("gender") or pdf_demographics.get("gender")
        if not pdf_blood_type:
            pdf_blood_type = prompt_demographics.get("blood_type") or pdf_demographics.get("blood_type")

        warnings = []
        if pdf_age in (None, ""):
            warnings.append("age_missing")
        if pdf_gender in (None, ""):
            warnings.append("gender_missing")
        if pdf_blood_type in (None, ""):
            warnings.append("blood_type_missing")

        combined_text = f"""PRIMARY SYMPTOMS:
{symptoms_prompt}

SUPPLEMENTARY MEDICAL INFORMATION FROM PDF:
{pdf_text}"""

        logger.info(
            "PDF triage: combining user symptoms with PDF content (symptoms: %d chars, PDF: %d chars)",
            len(symptoms_prompt),
            len(pdf_text),
        )

        prompt = build_pdf_triage_prompt(combined_text, age=pdf_age, gender=pdf_gender, blood_type=pdf_blood_type)
        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        try:
            ai_response = call_gemini_api(prompt, user_description="PDF upload triage")
            result = json.loads(ai_response)
        except Exception as e:
            logger.warning("Gemini AI error on PDF: %s", str(e))
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e),
            }, status=status.HTTP_502_BAD_GATEWAY)

        if isinstance(result, dict) and result.get("error"):
            logger.warning("AI unavailable for PDF. details=%s", result.get("details"))
            return Response({
                "error": "AI unavailable, staff review required",
                "message": "Our AI triage service is temporarily unavailable. Your case will be queued for staff review.",
                "details": result.get("details", []),
                "error_types": result.get("error_types", []),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        result = normalize_ai_response(result)
        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            response_data = dict(serializer.data)
            response_data["source"] = "ai"
            if warnings:
                response_data["warning"] = warnings

            enriched_output = dict(result)
            enriched_output["source"] = "ai"
            if warnings:
                enriched_output["warning"] = warnings
            _persist_ai_submission(
                request=request,
                symptoms=symptoms_prompt,
                ai_output=enriched_output,
                source="PDF_TRIAGE_ENDPOINT",
                extra_metadata={
                    "triage_inputs": {
                        "age": pdf_age,
                        "gender": pdf_gender,
                        "blood_type": pdf_blood_type,
                    },
                    "pdf_context": {
                        "file_name": getattr(pdf_file, "name", None),
                        "extracted_text_length": len(pdf_text),
                    },
                },
                photo_name=getattr(pdf_file, "name", None),
            )

            return Response(response_data)

        logger.warning("AI response validation failed. errors=%s", serializer.errors)
        return Response({
            "error": "AI response format error.",
            "message": "AI response did not match expected format.",
            "details": serializer.errors,
            "raw_ai": result,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TriageEvaluateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        symptoms = request.data.get("symptoms", "")
        if not symptoms:
            return Response({
                "error": "Missing symptoms.",
                "message": "Please provide a brief description of the patient's symptoms."
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(symptoms) > MAX_INPUT_LENGTH:
            return Response({
                "error": "Symptoms too long.",
                "message": f"Please limit your input to {MAX_INPUT_LENGTH} characters for best results."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = evaluate_triage(symptoms)
        except Exception as e:
            return Response({
                "error": "Evaluation error.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)
        if isinstance(result, dict) and "data" in result and "triage_result" in result["data"]:
            return Response(result["data"]["triage_result"])
        return Response(result)

# POST /api/v1/triage/
# ============================================================================

class TriageSubmissionView(APIView):
    """
    Main triage submission endpoint per API contract.
    
    POST /api/v1/triage/
    Request: {"description": "Chest pain..."}
    Response: Direct TriageItem shape (no envelope)
    """
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request):
        logger = logging.getLogger("triage.submission")
        
        # Get description from request (API contract field name)
        description = request.data.get("description") or request.data.get("symptoms")
        photo_name = request.data.get("photo_name")
        submitted_inputs = {
            key: _json_safe_value(request.data.get(key))
            for key in getattr(request.data, "keys", lambda: [])()
        }

        # Log triage submission attempt
        logger.info(f"Triage submission from user {request.user.id}")

        # Validate input using centralized validator
        if not description:
            logger.error(f"Description validation failed. Request data was: {request.data}")
            return Response({
                "code": "VALIDATION_ERROR",
                "message": "Description is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_description_length(description)
        except ValidationError as e:
            return Response({
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create Patient profile for user
            try:
                patient = request.user.patient_profile
            except Patient.DoesNotExist:
                patient = Patient.objects.create(
                    user=request.user,
                    name=request.user.username
                )

            # Call Member 6's triage service (complete logic)
            try:
                triage_result = evaluate_triage(description)
            except Exception as triage_error:
                logger.error(f"Triage evaluation failed for user {request.user.id}: {str(triage_error)}")
                return Response({
                    "code": "TRIAGE_ERROR",
                    "message": "Triage evaluation failed. Please try again later."
                }, status=status.HTTP_502_BAD_GATEWAY)

            # Extract data from Member 6's response format
            triage_data = triage_result.get("data", {}).get("triage_result", {})
            ai_contract = triage_result.get("data", {}).get("ai_contract", {})
            
            priority = triage_data.get("priority", 3)
            urgency_score = triage_data.get("urgency_score", 50)
            condition = ai_contract.get("condition", "Unknown")
            recommended_action = ai_contract.get("recommended_action")
            triage_status = triage_data.get("status", "waiting")
            is_critical = triage_data.get("is_critical", False)
            requires_immediate_attention = ai_contract.get("requires_immediate_attention", False)
            specialist_referral_suggested = ai_contract.get("specialist_referral_suggested", False)
            critical_keywords = ai_contract.get("critical_keywords", [])

            submission_metadata = {
                "submitted_inputs": submitted_inputs,
                "triage_inputs": {
                    "description": description,
                    "photo_name": photo_name,
                    "age": request.data.get("age"),
                    "gender": request.data.get("gender"),
                    "blood_type": request.data.get("blood_type"),
                },
                "ai_snapshot": {
                    "triage_result": triage_data,
                    "ai_contract": ai_contract,
                    "source": triage_result.get("data", {}).get("source", "GEMINI_AI"),
                },
            }

            # Save to database (Member 7's model) with enriched AI fields
            submission = PatientSubmission.objects.create(
                patient=patient,
                symptoms=description,  # Store in symptoms field
                photo_name=photo_name,
                priority=priority,
                urgency_score=urgency_score,
                condition=condition,
                is_critical=is_critical,
                requires_immediate_attention=requires_immediate_attention,
                specialist_referral_suggested=specialist_referral_suggested,
                critical_keywords=critical_keywords,
                status=triage_status,
                category=ai_contract.get("category"),
                explanation=ai_contract.get("explanation", []),
                reason=ai_contract.get("reason"),
                recommended_action=ai_contract.get("recommended_action"),
                confidence=ai_contract.get("confidence"),
                source=triage_result.get("data", {}).get("source", "GEMINI_AI"),
                metadata=submission_metadata,
            )

            # Broadcast WebSocket event (Member 8) - using correct function
            broadcast_patient_created(submission.id, priority, urgency_score)

            # Send notifications for new patient submissions
            try:
                # Notify patient about successful submission
                NotificationService.create_notification(
                    user=request.user,
                    notification_type="triage_status_change",
                    title="Triage Submission Received",
                    message=f"Your triage submission has been received and assigned priority {priority}. You will be notified of any status updates.",
                    metadata={
                        "submission_id": submission.id,
                        "priority": priority,
                        "condition": condition,
                        "recommended_action": recommended_action,
                        "action_type": "submission_created"
                    }
                )

                # For critical cases, notify all available staff immediately
                if priority == 1:
                    available_staff = User.objects.filter(role__in=["doctor", "nurse", "supervisor"])
                    NotificationService.create_bulk_notifications(
                        users=available_staff,
                        notification_type="critical_alert",
                        title="CRITICAL: Immediate Attention Required",
                        message=f"Critical patient submission (ID: {submission.id}) requires immediate medical attention. Condition: {condition}",
                        metadata={
                            "submission_id": submission.id,
                            "patient_id": patient.id,
                            "priority": priority,
                            "urgency_score": urgency_score,
                            "condition": condition,
                            "recommended_action": recommended_action,
                            "alert_type": "critical_submission"
                        }
                    )
            except Exception as notification_error:
                # Log notification errors but don't fail the submission
                logger.warning(f"Failed to send notifications for submission {submission.id}: {str(notification_error)}")

            # Log successful submission
            logger.info(f"Triage submission {submission.id} created with priority {priority}")

            # Return direct TriageItem shape (no envelope per API contract)
            return Response({
                "id": submission.id,
                "description": description,  # API field name
                "priority": priority,
                "recommended_action": recommended_action,
                "urgency_score": urgency_score,
                "condition": condition,
                "status": triage_status,
                "photo_name": photo_name,
                "created_at": submission.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Triage submission failed: {str(e)}")
            return Response({
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Triage processing failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
