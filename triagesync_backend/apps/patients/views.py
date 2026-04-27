from apps.patients.models import PatientSubmission
from django.db.models import Avg, Count
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.triage.models import TriageItem

from apps.triage.services.ai_service import analyze_symptoms
from apps.triage.services.triage_service import process_triage
from apps.realtime.services.broadcast_service import broadcast_new_triage
from triagesync_backend.apps.patients.serializers import TriageSubmissionSerializer

def get_patient_queue(priority=None, status=None):
    """
    Fetch patients with optional filtering.
    Always sorted by urgency_score DESC (critical first)
    """
    queryset = PatientSubmission.objects.all()

class PatientTriageView(APIView):
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
