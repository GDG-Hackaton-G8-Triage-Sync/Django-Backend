from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services.triage_service import evaluate_triage
from .serializers import TriageInputSerializer
from apps.authentication.permissions import IsDoctor
from apps.core.response import success_response, error_response


class TriageEvaluateView(APIView):

    def post(self, request):
        symptoms = request.data.get("symptoms")

        if not symptoms:
            return Response(
                {"error": "Symptoms are required"},
                status=400
            )

        result = evaluate_triage(symptoms)

        return Response(result)
