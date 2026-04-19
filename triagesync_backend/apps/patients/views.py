from rest_framework.views import APIView
from .serializers import PatientSubmissionSerializer
from rest_framework.permissions import IsAuthenticated


class PatientSubmissionView(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        serializer = TriageSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        symptoms = serializer.validated_data["symptoms"]

        # Create TriageItem (NEW CONTRACT MODEL)
        submission = TriageItem.objects.create(
            patient=request.user,
            description=symptoms,
            status="processing"
        )

        # AI + Logic
        ai_result = analyze_symptoms(symptoms)
        triage_result = process_triage(ai_result)

        # WebSocket event
        broadcast_new_triage({
            "type": "TRIAGE_CREATED",
            "data": {
                "id": submission.id,
                "urgency_score": triage_result.get("urgency_score", 0)
            }
        })

        
        return Response({
            "id": submission.id,
            "description": submission.description,
            "priority": triage_result.get("priority_level", 3),
            "urgency_score": triage_result.get("urgency_score", 0),
            "condition": triage_result.get("condition", "unknown"),
            "status": submission.status,
            "created_at": submission.created_at.isoformat()
        })