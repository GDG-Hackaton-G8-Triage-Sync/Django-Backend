from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PatientSubmissionSerializer
from rest_framework.permissions import IsAuthenticated

from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import PatientSubmission
import uuid

class PatientSubmissionView(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        serializer = PatientSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# /patient/triage/ endpoint
class PatientTriageView(APIView):
    def post(self, request):
        # Contract: {"symptoms": "string (max 500)", "language": "en", "attachments": ["file_123"]}
        symptoms = request.data.get("symptoms", "")
        language = request.data.get("language", "en")
        attachments = request.data.get("attachments", [])
        # Save submission (simplified, no file handling here)
        submission = PatientSubmission.objects.create(
            patient=request.user,
            symptoms=symptoms[:500],
        )
        # Generate session_id (mock)
        session_id = f"TS-{str(submission.id).zfill(4)}"
        return Response({
            "session_id": session_id,
            "status": "processing"
        }, status=status.HTTP_201_CREATED)

# /patient/triage/current/ endpoint
class PatientCurrentSessionView(APIView):
    def get(self, request):
        # Get latest submission for user
        submission = PatientSubmission.objects.filter(patient=request.user).order_by("-created_at").first()
        if not submission:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)
        session_id = f"TS-{str(submission.id).zfill(4)}"
        # Mock values for demo
        return Response({
            "session_id": session_id,
            "status": "in_queue",
            "priority_level": 2,
            "urgency_score": 85,
            "queue_position": 3,
            "estimated_wait_minutes": 14
        })

# /patient/triage/upload/ endpoint
class PatientFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": {"code": "validation_error", "message": "No file uploaded."}}, status=status.HTTP_400_BAD_REQUEST)
        # Generate file_id and mock URL
        file_id = f"file_{uuid.uuid4()}"
        url = f"https://cdn.triagesync.com/{file_id}.jpg"
        # (In production, save file and store metadata)
        return Response({
            "file_id": file_id,
            "url": url
        }, status=status.HTTP_201_CREATED)
