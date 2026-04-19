# New AI-based triage endpoint
from .services.ai_service import get_triage_recommendation
from .serializers import TriageAIResponseSerializer
from rest_framework import status

from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging

from .services.triage_service import evaluate_triage

MAX_INPUT_LENGTH = 500

class TriageAIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        patient_description = request.data.get("description")
        if not patient_description:
            return Response({
                "error": "Missing description.",
                "message": "Please provide a brief description of the patient's symptoms."
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(patient_description) > MAX_INPUT_LENGTH:
            return Response({
                "error": "Description too long.",
                "message": f"Please limit your input to {MAX_INPUT_LENGTH} characters for best results."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = get_triage_recommendation(patient_description)
        except Exception as e:
            return Response({
                "error": "AI service unavailable.",
                "message": "We are unable to process your request at this time. Please try again later.",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

        # If the AI returned an error object, handle it gracefully (match error string or error_types)
        if isinstance(result, dict) and result.get("error"):
            return Response({
                "error": "AI unavailable.",
                "message": "Sorry, the AI service is currently unavailable or over quota. Your case will be flagged for staff review. No automated triage decision could be made.",
                "details": result.get("details", []),
                "user_description": result.get("user_description", "")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Only pass expected fields to the serializer
        expected_fields = [
            "priority_level", "urgency_score", "condition", "category", "is_critical", "explanation"
        ]
        filtered_result = {k: v for k, v in result.items() if k in expected_fields}
        serializer = TriageAIResponseSerializer(data=filtered_result)
        if serializer.is_valid():
            return Response(serializer.data)
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
