import re as _re

def is_relevant(text):
    if not text or not isinstance(text, str):
        return False
    keywords = [
        "pain", "fever", "cough", "fracture", "bleeding", "shortness of breath", "dizzy", "vomiting", "rash", "injury", "trauma", "stroke", "cardiac", "chest", "headache", "infection", "wound", "burn", "swelling", "seizure", "unconscious", "weakness", "nausea", "diarrhea", "palpitation", "collapse"
    ]
    text_lower = text.lower()
    return any(_re.search(r"\b" + _re.escape(kw) + r"\b", text_lower) for kw in keywords)

# New AI-based triage endpoint
from .services.ai_service import get_triage_recommendation
from .serializers import TriageAIResponseSerializer
from .serializers import PDFUploadSerializer
from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging

from .serializers import TriageAIResponseSerializer
from .services.prompt_engine import build_pdf_triage_prompt
from .services.ai_service import call_gemini_api
from .services.fallback_service import compute_fallback_triage
import json

from PyPDF2 import PdfReader


from .services.triage_service import evaluate_triage

MAX_INPUT_LENGTH = 500

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
            result = get_triage_recommendation(symptoms, age=age, gender=gender)
        except Exception as e:
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

        ai_failed_details = None
        if isinstance(result, dict) and result.get("error"):
            logger = logging.getLogger("triage.ai")
            logger.warning("AI unavailable, using deterministic fallback. details=%s", result.get("details"))
            ai_failed_details = result.get("details", [])
            result = compute_fallback_triage(symptoms, age=age, gender=gender)

        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            response_data = dict(serializer.data)
            response_data["source"] = result.get("source", "ai")
            if ai_failed_details:
                response_data["ai_details"] = ai_failed_details
            if warning:
                response_data["warning"] = warning
            return Response(response_data)

        # Serializer failed -- AI returned malformed output. Run fallback as last resort.
        logger = logging.getLogger("triage.ai")
        logger.warning("AI response validation failed, using fallback. errors=%s", serializer.errors)
        fb = compute_fallback_triage(symptoms, age=age, gender=gender)
        fb_filtered = {k: v for k, v in fb.items() if k in expected_fields}
        fb_serializer = TriageAIResponseSerializer(data=fb_filtered)
        if fb_serializer.is_valid():
            response_data = dict(fb_serializer.data)
            response_data["source"] = fb["source"]
            response_data["ai_details"] = ["AI returned malformed response"]
            return Response(response_data)
        return Response({
            "error": "AI response format error.",
            "message": "Sorry, we could not interpret the AI's response. Your case will be flagged for staff review.",
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
        # Build prompt and call Gemini
        prompt = build_pdf_triage_prompt(text)
        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        ai_failed_details = None
        try:
            ai_response = call_gemini_api(prompt, user_description="PDF upload triage")
            result = json.loads(ai_response)
        except Exception as e:
            logger.warning("Gemini AI error, using fallback: %s", str(e))
            ai_failed_details = [str(e)]
            result = compute_fallback_triage(text)

        if isinstance(result, dict) and result.get("error"):
            logger.warning("AI unavailable for PDF, using fallback. details=%s", result.get("details"))
            ai_failed_details = result.get("details", [])
            result = compute_fallback_triage(text)

        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            response_data = dict(serializer.data)
            response_data["source"] = result.get("source", "ai")
            if ai_failed_details:
                response_data["ai_details"] = ai_failed_details
            return Response(response_data)

        # Serializer failed -- AI returned malformed output. Run fallback as last resort.
        logger.warning("AI response validation failed, using fallback. errors=%s", serializer.errors)
        fb = compute_fallback_triage(text)
        fb_filtered = {k: v for k, v in fb.items() if k in expected_fields}
        fb_serializer = TriageAIResponseSerializer(data=fb_filtered)
        if fb_serializer.is_valid():
            response_data = dict(fb_serializer.data)
            response_data["source"] = fb["source"]
            response_data["ai_details"] = ["AI returned malformed response"]
            return Response(response_data)
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
        return Response(result)
