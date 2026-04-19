from rest_framework.response import Response
from rest_framework.views import APIView

from .services.triage_service import evaluate_triage


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