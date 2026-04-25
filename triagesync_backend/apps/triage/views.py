from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services.triage_service import evaluate_triage
from .serializers import TriageInputSerializer
from apps.authentication.permissions import IsDoctor
from apps.core.response import success_response, error_response


class TriageEvaluateView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        serializer = TriageInputSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        symptoms = serializer.validated_data["symptoms"]

        try:
            result = evaluate_triage(symptoms)

            return success_response(result)

        except Exception:
            
            return error_response(
                {"message": "Triage processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
