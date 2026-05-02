from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from triagesync_backend.apps.authentication.permissions import IsStaffOrAdmin, IsAdmin

class ClinicalVerificationView(APIView):
    """
    Digital signature for clinical triage verification.
    PATCH /api/v1/triage/{id}/verify/
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, submission_id):
        user = request.user
        if user.role not in ['doctor', 'nurse', 'admin']:
            return error_response(
                code="PERMISSION_DENIED",
                message="Only clinical staff can verify triage results.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            submission.verified_by_user = user
            submission.verified_at = timezone.now()
            submission.save()
            
            return Response({
                "message": "Triage verified successfully",
                "verified_at": submission.verified_at,
                "verified_by": user.username
            }, status=status.HTTP_200_OK)
        except PatientSubmission.DoesNotExist:
            return not_found_response("Submission not found")


class StaffNoteView(APIView):
    """
    Internal staff notes and observations.
    POST /api/v1/triage/{id}/notes/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        # Staff can see all notes, patients only non-internal notes (if allowed)
        user = request.user
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            # If patient, verify they own the submission
            if user.role == 'patient' and submission.patient.user != user:
                return error_response(code="ACCESS_DENIED", status_code=403, message="Not your submission")
            
            notes = submission.notes.all()
            if user.role == 'patient':
                notes = notes.filter(is_internal=False)
            
            serializer = StaffNoteSerializer(notes, many=True)
            return Response(serializer.data)
        except PatientSubmission.DoesNotExist:
            return not_found_response()

    def post(self, request, submission_id):
        user = request.user
        if user.role not in ['doctor', 'nurse', 'admin']:
            return error_response(code="PERMISSION_DENIED", status_code=403, message="Staff only")
            
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            serializer = StaffNoteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(submission=submission, author=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PatientSubmission.DoesNotExist:
            return not_found_response()


class StaffAssignmentView(APIView):
    """
    Assign staff member to a triage record.
    PATCH /api/v1/triage/{id}/assign/
    """
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, submission_id):
        user = request.user
        if user.role not in ['doctor', 'nurse', 'admin']:
            return error_response(code="PERMISSION_DENIED", status_code=403, message="Staff only")
            
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            submission.assigned_to = user
            submission.status = PatientSubmission.Status.IN_PROGRESS
            submission.save()
            
            return Response({
                "message": f"Assigned to {user.username}",
                "status": submission.status
            })
        except PatientSubmission.DoesNotExist:
            return not_found_response()


class VitalsHistoryView(APIView):
    """
    Historical vitals chronology.
    GET /api/v1/triage/{id}/vitals/history/
    POST /api/v1/triage/{id}/vitals/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            # Verify ownership if patient
            if request.user.role == 'patient' and submission.patient.user != request.user:
                return error_response(code="ACCESS_DENIED", status_code=403, message="Forbidden")
                
            vitals = submission.vitals_history.all()
            serializer = VitalsLogSerializer(vitals, many=True)
            return Response(serializer.data)
        except PatientSubmission.DoesNotExist:
            return not_found_response()

    def post(self, request, submission_id):
        if request.user.role not in ['doctor', 'nurse', 'admin']:
            return error_response(code="PERMISSION_DENIED", status_code=403, message="Staff only")
            
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            serializer = VitalsLogSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(submission=submission, recorded_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PatientSubmission.DoesNotExist:
            return not_found_response()
