from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services.triage_service import evaluate_triage
from .serializers import TriageInputSerializer
from apps.authentication.permissions import IsDoctor


class TriageEvaluateView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        serializer = TriageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        symptoms = serializer.validated_data["symptoms"]

        try:
            result = evaluate_triage(symptoms)

            return Response({
                "success": True,
                "data": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
