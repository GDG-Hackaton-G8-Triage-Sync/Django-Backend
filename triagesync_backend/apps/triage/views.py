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
        def is_relevant(text):
            if not text or not isinstance(text, str):
                return False
            keywords = [
                "pain", "fever", "cough", "fracture", "bleeding", "shortness of breath", "dizzy", "vomiting", "rash", "injury", "trauma", "stroke", "cardiac", "chest", "headache", "infection", "wound", "burn", "swelling", "seizure", "unconscious", "weakness", "nausea", "diarrhea", "palpitation", "collapse", "emergency", "urgent", "medical"
            ]
            text_lower = text.lower()
            return any(kw in text_lower for kw in keywords)
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

        if isinstance(result, dict) and result.get("error"):
            return Response({
                "error": "AI unavailable.",
                "message": "Sorry, the AI service is currently unavailable or over quota. Your case will be flagged for staff review. No automated triage decision could be made.",
                "details": result.get("details", []),
                "user_description": result.get("user_description", "")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
        ]
        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            response_data = serializer.data
            if warning:
                response_data["warning"] = warning
            return Response(response_data)
        else:
            logger = logging.getLogger("triage.ai")
            logger.error("AI response validation failed. Raw AI result: %%r", result)
            print("[DEBUG] AI response validation failed. Raw AI result:", repr(result))
            return Response({
                "error": "AI response format error.",
                "message": "Sorry, we could not interpret the AI's response. Your case will be flagged for staff review.",
                "details": serializer.errors,
                "raw_ai": result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# PDF upload and Gemini extraction endpoint
class TriagePDFExtractView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PDFUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        pdf_file = serializer.validated_data['file']
        try:
            reader = PdfReader(pdf_file)
            text = "\n".join(page.extract_text() or '' for page in reader.pages)
        except Exception as e:
            return Response({
                "error": "PDF extraction failed.",
                "message": "Could not extract text from the PDF.",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        # Truncate text if extremely long (e.g., 10,000 chars)
        max_text_length = 10000
        if len(text) > max_text_length:
            text = text[:max_text_length]
        # If no text extracted, return error
        if not text.strip():
            return Response({
                "error": "No text extracted.",
                "message": "No extractable text found in the PDF. Please upload a PDF with selectable text."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Reject if text is not relevant
        def is_relevant(text):
            if not text or not isinstance(text, str):
                return False
            keywords = [
                "pain", "fever", "cough", "fracture", "bleeding", "shortness of breath", "dizzy", "vomiting", "rash", "injury", "trauma", "stroke", "cardiac", "chest", "headache", "infection", "wound", "burn", "swelling", "seizure", "unconscious", "weakness", "nausea", "diarrhea", "palpitation", "collapse", "emergency", "urgent", "medical"
            ]
            text_lower = text.lower()
            return any(kw in text_lower for kw in keywords)
        if not is_relevant(text):
            return Response({
                "error": "PDF not relevant.",
                "message": "The uploaded PDF does not contain relevant medical information for triage. Please upload a document related to patient symptoms or medical conditions."
            }, status=status.HTTP_400_BAD_REQUEST)
        # Build prompt and call Gemini
        prompt = build_pdf_triage_prompt(text)
        try:
            ai_response = call_gemini_api(prompt, user_description="PDF upload triage")
            # Try to parse and filter AI response
            result = json.loads(ai_response)
            expected_fields = [
                "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation", "recommended_action", "reason"
            ]
            filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        except Exception as e:
            return Response({
                "error": "Gemini AI error.",
                "message": "Failed to get a valid response from Gemini.",
                "details": str(e),
                "raw_ai": ai_response if 'ai_response' in locals() else None
            }, status=status.HTTP_502_BAD_GATEWAY)
        # Validate with serializer
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response({
                "error": "AI response format error.",
                "message": "AI response did not match expected format.",
                "details": serializer.errors,
                "raw_ai": result
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
