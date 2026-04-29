from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from triagesync_backend.apps.authentication.permissions import IsPatient
from triagesync_backend.apps.core.pagination import StandardResultsSetPagination
from triagesync_backend.apps.core.response import error_response, not_found_response
from .models import Patient, PatientSubmission
from .serializers import PatientSubmissionSerializer

import logging

logger = logging.getLogger(__name__)


class PatientProfileView(APIView):
    """
    Patient profile management endpoint.
    
    GET /api/v1/patients/profile/ - Get patient profile
    PATCH /api/v1/patients/profile/ - Update patient profile
    """
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get_or_create_patient(self, user):
        """Get or create patient profile for user."""
        try:
            return user.patient_profile
        except Patient.DoesNotExist:
            patient = Patient.objects.create(
                user=user,
                name=user.username
            )
            logger.info(f"Created patient profile for user {user.id}")
            return patient
    
    def get(self, request):
        """Get authenticated patient's profile."""
        patient = self.get_or_create_patient(request.user)
        return Response({
            "id": patient.id,
            "name": patient.name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "contact_info": patient.contact_info,
            "user_id": patient.user.id,
            "username": patient.user.username,
            "email": patient.user.email,
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update authenticated patient's profile."""
        patient = self.get_or_create_patient(request.user)
        
        # Update allowed fields
        if 'name' in request.data:
            patient.name = request.data['name']
        if 'date_of_birth' in request.data:
            # Handle date_of_birth - can be string or date object
            dob = request.data['date_of_birth']
            if dob:
                from datetime import datetime
                if isinstance(dob, str):
                    # Parse ISO format date string
                    try:
                        patient.date_of_birth = datetime.fromisoformat(dob).date()
                    except (ValueError, AttributeError):
                        # If parsing fails, try to set it directly (Django will handle validation)
                        patient.date_of_birth = dob
                else:
                    patient.date_of_birth = dob
            else:
                patient.date_of_birth = None
        if 'contact_info' in request.data:
            patient.contact_info = request.data['contact_info']
        
        patient.save()
        logger.info(f"Updated patient profile {patient.id}")
        
        return Response({
            "id": patient.id,
            "name": patient.name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "contact_info": patient.contact_info,
            "user_id": patient.user.id,
            "username": patient.user.username,
            "email": patient.user.email,
        }, status=status.HTTP_200_OK)


class PatientHistoryView(APIView):
    """
    Patient submission history endpoint with pagination.
    
    GET /api/v1/patients/history/ - Get all patient's triage submissions
    Query params: page, page_size (default 20, max 100)
    """
    permission_classes = [IsAuthenticated, IsPatient]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        """Get authenticated patient's submission history with pagination."""
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            # No patient profile means no submissions
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            }, status=status.HTTP_200_OK)
        
        # Get all submissions for this patient, ordered by most recent first
        submissions = PatientSubmission.objects.filter(
            patient=patient
        ).order_by('-created_at')
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_submissions = paginator.paginate_queryset(submissions, request)
        
        # Use PatientSubmissionSerializer for patient-facing history
        serializer = PatientSubmissionSerializer(paginated_submissions, many=True)
        return paginator.get_paginated_response(serializer.data)


class PatientSubmissionDetailView(APIView):
    """
    Patient submission detail endpoint.
    
    GET /api/v1/patients/submissions/{id}/ - Get specific submission details
    """
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get(self, request, submission_id):
        """Get specific submission details for authenticated patient."""
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return not_found_response("Patient profile not found")
        
        try:
            # Ensure submission belongs to this patient
            submission = PatientSubmission.objects.get(
                id=submission_id,
                patient=patient
            )
        except PatientSubmission.DoesNotExist:
            return not_found_response("Submission not found")
        
        # Use PatientSubmissionSerializer for patient-facing detail
        serializer = PatientSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientCurrentSessionView(APIView):
    """
    Patient current/active session endpoint.
    
    GET /api/v1/patients/current/ - Get patient's most recent active submission
    """
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get(self, request):
        """Get patient's most recent active (non-completed) submission."""
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response({
                "current_submission": None,
                "message": "No active session"
            }, status=status.HTTP_200_OK)
        
        # Get most recent non-completed submission
        active_submission = PatientSubmission.objects.filter(
            patient=patient,
            status__in=[PatientSubmission.Status.WAITING, PatientSubmission.Status.IN_PROGRESS]
        ).order_by('-created_at').first()
        
        if not active_submission:
            return Response({
                "current_submission": None,
                "message": "No active session"
            }, status=status.HTTP_200_OK)
        
        return Response({
            "current_submission": {
                "id": active_submission.id,
                "symptoms": active_submission.symptoms,
                "priority": active_submission.priority,
                "urgency_score": active_submission.urgency_score,
                "condition": active_submission.condition,
                "status": active_submission.status,
                "photo_name": active_submission.photo_name,
                "created_at": active_submission.created_at.isoformat(),
                "processed_at": active_submission.processed_at.isoformat() if active_submission.processed_at else None,
            },
            "message": "Active session found"
        }, status=status.HTTP_200_OK)




class TriageSubmissionsHistoryView(APIView):
    """
    Triage submissions history retrieval endpoint.
    
    GET /api/v1/triage-submissions/
    - Patients: Returns only their own submissions
    - Staff: Returns all submissions or filtered by email query param
    
    Query params:
        - email (optional): Filter by patient email (staff only)
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retrieve triage submissions based on user role."""
        from triagesync_backend.apps.authentication.models import User
        from .serializers import TriageSubmissionHistorySerializer
        
        user = request.user
        
        if user.role == 'patient':
            # Patients see only their own submissions
            try:
                patient = Patient.objects.get(user=user)
                submissions = PatientSubmission.objects.filter(patient=patient)
            except Patient.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        else:
            # Staff can see all submissions or filter by email
            email = request.query_params.get('email', None)
            
            if email:
                # Filter by patient email
                try:
                    patient_user = User.objects.get(email=email)
                    patient = Patient.objects.get(user=patient_user)
                    submissions = PatientSubmission.objects.filter(patient=patient)
                except (User.DoesNotExist, Patient.DoesNotExist):
                    return Response([], status=status.HTTP_200_OK)
            else:
                # Return all submissions
                submissions = PatientSubmission.objects.all()
        
        # Serialize and return as direct array
        serializer = TriageSubmissionHistorySerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
