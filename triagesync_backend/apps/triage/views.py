import re as _re
import json

# New AI-based triage endpoint
from .services.ai_service import get_triage_recommendation
from .serializers import TriageAIResponseSerializer
from .serializers import PDFUploadSerializer
from .serializers import TriageSubmissionSerializer
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
    normalize_blood_type,
    normalize_gender,
)
from PyPDF2 import PdfReader

from .services.triage_service import evaluate_triage
# from .serializers import TriageInputSerializer  # Removed: does not exist
from triagesync_backend.apps.authentication.permissions import IsDoctor, IsPatient, IsStaffOrAdmin
from triagesync_backend.apps.core.response import success_response, error_response
from triagesync_backend.apps.core.validators import validate_description_length, validate_photo_name
from triagesync_backend.apps.dashboard.services.dashboard_service import get_waiting_analytics

# Required imports for TriageSubmissionView
from triagesync_backend.apps.patients.models import PatientSubmission, Patient
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_patient_created
from triagesync_backend.apps.notifications.services.notification_service import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()

MAX_INPUT_LENGTH = 500

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
        # Use sanitized data and warnings from middleware
        warning = getattr(request, "_triage_warning", None)
        error = getattr(request, "_triage_error", None)
        data = request.data
        symptoms = data.get("symptoms")
        age = data.get("age")
        gender = data.get("gender")
        blood_type = data.get("blood_type")
        # If not provided, get from patient profile (if authenticated)
        if not age or not gender or not blood_type:
            user = request.user if request.user and request.user.is_authenticated else None
            if user and hasattr(user, "patient_profile"):
                patient = user.patient_profile
                if not age and getattr(patient, "age", None) is not None:
                    age = patient.age
                if not gender and getattr(patient, "gender", None):
                    gender = patient.gender
                if not blood_type and getattr(patient, "blood_type", None):
                    blood_type = patient.blood_type
        if error:
            return Response({
                "error": "Missing symptoms.",
                "message": "Please provide at least one symptom to proceed."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Optionally, check input length if symptoms is a string
        if isinstance(symptoms, str) and len(symptoms) > MAX_INPUT_LENGTH:
            return Response({
                "error": "Symptoms too long.",
                "message": f"Please limit your input to {MAX_INPUT_LENGTH} characters for best results."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Reject if symptoms is empty or not relevant
        if not is_relevant(symptoms):
            return Response({
                "error": "Input not relevant.",
                "message": "Please provide symptoms or information related to a medical triage situation."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = get_triage_recommendation(symptoms, age=age, gender=gender, blood_type=blood_type)
        except Exception as e:
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

        # AI returned an error envelope (all models failed, circuit open, etc.)
        # The decision of whether/how to substitute rule-based output is M6's
        # responsibility ("fallback system" in the task distribution), so here
        # we surface the error cleanly and let the caller decide.
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
            if warning:
                response_data["warning"] = warning
            # Return flat structure (no envelope)
            return Response(response_data)

        logger = logging.getLogger("triage.ai")
        logger.warning("AI response validation failed. errors=%s", serializer.errors)
        return Response({
            "error": "AI response format error.",
            "message": "AI response did not match expected format.",
            "details": serializer.errors,
            "raw_ai": result,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# PDF upload and Gemini extraction endpoint
class TriagePDFExtractView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        import logging
        logger = logging.getLogger("triage.pdf")
        serializer = PDFUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("PDF upload: invalid serializer input: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        pdf_file = serializer.validated_data['file']
        # Check for empty file
        if not pdf_file or getattr(pdf_file, 'size', None) == 0:
            logger.warning("PDF upload: empty file uploaded.")
            return Response({
                "error": "Empty file.",
                "message": "The uploaded file is empty. Please upload a valid PDF document."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Check file extension
        if not getattr(pdf_file, 'name', '').lower().endswith('.pdf'):
            logger.warning("PDF upload: non-PDF file uploaded: %s", getattr(pdf_file, 'name', ''))
            return Response({
                "error": "Only PDF files are allowed.",
                "message": "Please upload a file with a .pdf extension."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Try to read PDF
        try:
            reader = PdfReader(pdf_file)
            text = "\n".join(page.extract_text() or '' for page in reader.pages)
        except Exception as e:
            logger.warning("PDF extraction failed: %s", str(e))
            return Response({
                "error": "PDF extraction failed.",
                "message": "Could not extract text from the PDF. Please ensure the file is a valid, non-corrupted PDF.",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        # Truncate text if extremely long (e.g., 10,000 chars)
        max_text_length = 10000
        if len(text) > max_text_length:
            text = text[:max_text_length]
        # If no text extracted, return error
        if not text or not text.strip():
            logger.warning("PDF upload: no extractable text found.")
            return Response({
                "error": "No text extracted.",
                "message": "No extractable text found in the PDF. Please upload a PDF with selectable text."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Reject if text is not relevant
        if not is_relevant(text):
            logger.warning("PDF upload: irrelevant content rejected.")
            return Response({
                "error": "PDF not relevant.",
                "message": "The uploaded PDF does not contain relevant medical information for triage. Please upload a document related to patient symptoms or medical conditions."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Build prompt and call Gemini -- carry demographics from the multipart form if present
        pdf_age = normalize_age(request.data.get("age"))
        pdf_gender = normalize_gender(request.data.get("gender"))
        pdf_blood_type = request.data.get("blood_type")
        # If not provided, get from patient profile (if authenticated)
        user = request.user if request.user and request.user.is_authenticated else None
        if user and hasattr(user, "patient_profile"):
            patient = user.patient_profile
            if not pdf_age and getattr(patient, "age", None) is not None:
                pdf_age = patient.age
            if not pdf_gender and getattr(patient, "gender", None):
                pdf_gender = patient.gender
            if not pdf_blood_type and getattr(patient, "blood_type", None):
                pdf_blood_type = patient.blood_type
        prompt = build_pdf_triage_prompt(text, age=pdf_age, gender=pdf_gender, blood_type=pdf_blood_type)
        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        try:
            ai_response = call_gemini_api(prompt, user_description="PDF upload triage")
            result = json.loads(ai_response)
        except Exception as e:
            # AI call or JSON decode failed -- surface as 502. Rule-based
            # fallback substitution is M6's responsibility (triage_service).
            logger.warning("Gemini AI error on PDF: %s", str(e))
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e),
            }, status=status.HTTP_502_BAD_GATEWAY)

        # AI returned a structured error envelope (all models failed, circuit open).
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
            # Return flat structure (no envelope)
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
        # Flatten envelope if present
        if isinstance(result, dict) and "data" in result and "triage_result" in result["data"]:
            flat_result = result["data"]["triage_result"]
            return Response(flat_result)
        return Response(result)


def _build_submission_triage(description, patient, submitted_blood_type=None):
    """
    Resolve triage with demographics when available, then fall back to the
    existing rule-based evaluation flow if AI is unavailable.
    """
    result = get_triage_recommendation(
        description,
        age=getattr(patient, "age", None),
        gender=getattr(patient, "gender", None),
        blood_type=submitted_blood_type or getattr(patient, "blood_type", None),
    )

    if isinstance(result, dict) and not result.get("error"):
        urgency_score = result.get("urgency_score", 50)
        priority = result.get("priority_level")
        if priority is None:
            if urgency_score >= 80:
                priority = 1
            elif urgency_score >= 60:
                priority = 2
            elif urgency_score >= 40:
                priority = 3
            elif urgency_score >= 20:
                priority = 4
            else:
                priority = 5

        return {
            "priority": priority,
            "urgency_score": urgency_score,
            "condition": result.get("condition", "Unknown"),
            "category": result.get("category", "General"),
            "is_critical": result.get("is_critical", priority == 1),
            "explanation": result.get("explanation", []),
            "recommended_action": result.get("recommended_action"),
            "reason": result.get("reason"),
            "confidence": round(float(urgency_score or 0) / 100, 2),
            "source": "ai",
        }

    fallback = evaluate_triage(description)
    fallback_data = fallback.get("data", {})
    triage_result = fallback_data.get("triage_result", {})
    ai_contract = fallback_data.get("ai_contract", {})

    urgency_score = triage_result.get("urgency_score", 50)
    return {
        "priority": triage_result.get("priority", 3),
        "urgency_score": urgency_score,
        "condition": ai_contract.get("condition", "Unknown"),
        "category": ai_contract.get("category", "General"),
        "is_critical": triage_result.get("is_critical", False),
        "explanation": ai_contract.get("explanation", []),
        "recommended_action": ai_contract.get("recommended_action"),
        "reason": ai_contract.get("reason"),
        "confidence": round(float(urgency_score or 0) / 100, 2),
        "source": fallback_data.get("source", "fallback"),
    }


class TriageWaitingAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            submission = PatientSubmission.objects.select_related("patient__user").get(id=id)
        except PatientSubmission.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="Submission not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if request.user.is_patient() and submission.patient.user_id != request.user.id:
            return error_response(
                code="FORBIDDEN",
                message="You do not have access to this submission",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not request.user.is_patient() and not (request.user.is_admin() or request.user.is_medical_staff()):
            return error_response(
                code="FORBIDDEN",
                message="You do not have access to this resource",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return Response(get_waiting_analytics(submission))


# ============================================================================
# MAIN TRIAGE SUBMISSION ENDPOINT (API Contract Compliant)
# POST /api/v1/triage/
# ============================================================================

class TriageSubmissionView(APIView):
    """
    Main triage submission endpoint per API contract.
    """

    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request):
        logger = logging.getLogger("triage.submission")
        description = request.data.get("description")
        photo_name = request.data.get("photo_name")
        uploaded_photo = request.FILES.get("photo")
        blood_type = request.data.get("blood_type")

        logger.info("Triage submission from user %s", request.user.id)

        if not description:
            return Response(
                {"code": "VALIDATION_ERROR", "message": "Description is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_description_length(description)
            if photo_name:
                validate_photo_name(photo_name)
        except ValidationError as e:
            return Response(
                {"code": "VALIDATION_ERROR", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            try:
                patient = request.user.patient_profile
            except Patient.DoesNotExist:
                patient = Patient.objects.create(
                    user=request.user,
                    name=request.user.username,
                )

            normalized_blood_type = normalize_blood_type(blood_type) if blood_type else None
            if blood_type and not normalized_blood_type:
                return Response(
                    {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid blood type. Use one of: A+, A-, B+, B-, AB+, AB-, O+, O-.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if normalized_blood_type and patient.blood_type != normalized_blood_type:
                patient.blood_type = normalized_blood_type
                patient.save(update_fields=["blood_type"])

            triage_payload = _build_submission_triage(description, patient, normalized_blood_type)
            if uploaded_photo and not photo_name:
                photo_name = uploaded_photo.name

            submission = PatientSubmission.objects.create(
                patient=patient,
                symptoms=description,
                photo_name=photo_name,
                photo=uploaded_photo,
                priority=triage_payload["priority"],
                urgency_score=triage_payload["urgency_score"],
                condition=triage_payload["condition"],
                category=triage_payload["category"],
                status=PatientSubmission.Status.WAITING,
                is_critical=triage_payload["is_critical"],
                explanation=triage_payload["explanation"],
                recommended_action=triage_payload["recommended_action"],
                reason=triage_payload["reason"],
                confidence=triage_payload["confidence"],
                source=triage_payload["source"],
            )

            broadcast_patient_created(submission)

            try:
                NotificationService.create_notification(
                    user=request.user,
                    notification_type="triage_status_change",
                    title="Triage Submission Received",
                    message=(
                        f"Your triage submission has been received and assigned "
                        f"priority {submission.priority}. You will be notified of any status updates."
                    ),
                    metadata={
                        "submission_id": submission.id,
                        "priority": submission.priority,
                        "condition": submission.condition,
                        "action_type": "submission_created",
                    },
                )

                if submission.priority == 1:
                    available_staff = User.objects.filter(role__in=["admin", "doctor", "nurse", "staff"])
                    NotificationService.create_bulk_notifications(
                        users=available_staff,
                        notification_type="critical_alert",
                        title="CRITICAL: Immediate Attention Required",
                        message=(
                            f"Critical patient submission (ID: {submission.id}) requires "
                            f"immediate medical attention. Condition: {submission.condition}"
                        ),
                        metadata={
                            "submission_id": submission.id,
                            "patient_id": patient.id,
                            "priority": submission.priority,
                            "urgency_score": submission.urgency_score,
                            "condition": submission.condition,
                            "alert_type": "critical_submission",
                        },
                    )
            except Exception as notification_error:
                logger.warning(
                    "Failed to send notifications for submission %s: %s",
                    submission.id,
                    notification_error,
                )

            logger.info(
                "Triage submission %s created with priority %s",
                submission.id,
                submission.priority,
            )

            serializer = TriageSubmissionSerializer(submission, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Triage submission failed: %s", str(e))
            return Response(
                {"code": "INTERNAL_SERVER_ERROR", "message": "Triage processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
