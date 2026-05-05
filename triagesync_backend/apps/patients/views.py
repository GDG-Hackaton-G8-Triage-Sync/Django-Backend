from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes

from triagesync_backend.apps.authentication.permissions import IsPatient
from triagesync_backend.apps.core.pagination import StandardResultsSetPagination
from triagesync_backend.apps.core.response import error_response, not_found_response
from .models import Patient, PatientSubmission
from .serializers import PatientSubmissionSerializer
from .utils import validate_profile_photo
from triagesync_backend.apps.dashboard.services.wait_time_service import calculate_wait_time, get_sla_status
from triagesync_backend.apps.core.serializers import ErrorResponseSerializer
from triagesync_backend.apps.authentication.serializers import GenericProfileSerializer

import logging

logger = logging.getLogger(__name__)

ACTIVE_QUEUE_STATUSES = [PatientSubmission.Status.WAITING, PatientSubmission.Status.IN_PROGRESS]


def _get_active_queue_queryset():
    return PatientSubmission.objects.select_related(
        "patient__user",
        "assigned_to",
        "verified_by_user",
    ).filter(status__in=ACTIVE_QUEUE_STATUSES).order_by("priority", "-urgency_score", "created_at")


def _build_queue_steps(status):
    steps = [
        {"key": "submitted", "label": "Submitted", "completed": True},
        {"key": "waiting", "label": "Waiting", "completed": status in [PatientSubmission.Status.WAITING, PatientSubmission.Status.IN_PROGRESS, PatientSubmission.Status.COMPLETED]},
        {"key": "in_review", "label": "In review", "completed": status in [PatientSubmission.Status.IN_PROGRESS, PatientSubmission.Status.COMPLETED]},
        {"key": "being_seen", "label": "Being seen", "completed": status in [PatientSubmission.Status.IN_PROGRESS, PatientSubmission.Status.COMPLETED]},
        {"key": "completed", "label": "Completed", "completed": status == PatientSubmission.Status.COMPLETED},
    ]

    if status == PatientSubmission.Status.WAITING:
        current_step = "Waiting"
        progress_percent = 30
        status_label = "Waiting for staff review"
    elif status == PatientSubmission.Status.IN_PROGRESS:
        current_step = "Being seen"
        progress_percent = 75
        status_label = "A clinician is reviewing your case"
    else:
        current_step = "Completed"
        progress_percent = 100
        status_label = "Your case is complete"

    return {
        "current_step": current_step,
        "progress_percent": progress_percent,
        "status_label": status_label,
        "steps": steps,
    }


def _estimate_wait_range_minutes(submission, queue_position, total_active_cases):
    from triagesync_backend.apps.dashboard.services.wait_time_service import get_wait_time_analytics

    analytics = get_wait_time_analytics()

    # Prefer recent completed-case average as per-case turnover baseline; fall back to avg active wait
    per_case_minutes = analytics.get("avg_wait_completed_24h") or analytics.get("avg_wait_active") or 20

    # Base by priority bands but keep narrower bands and blend with analytics
    base_bands = {1: (0, 8), 2: (8, 18), 3: (18, 30), 4: (30, 50), 5: (50, 90)}
    base_min, base_max = base_bands.get(submission.priority, (15, 30))

    ahead = max((queue_position or 1) - 1, 0)

    # Add expected time for cases ahead using average per-case handling time
    added_min = ahead * int(per_case_minutes * 0.7)
    added_max = ahead * int(per_case_minutes * 1.0)

    min_minutes = max(0, base_min + added_min)
    max_minutes = base_max + added_max

    # If case already in progress, reduce lower bound
    if submission.status == PatientSubmission.Status.IN_PROGRESS:
        min_minutes = max(0, int(min_minutes * 0.5))
        max_minutes = max(min_minutes + 5, int(max_minutes * 0.8))

    return {
        "min_minutes": int(min_minutes),
        "max_minutes": int(max_minutes),
        "label": f"About {int(min_minutes)}-{int(max_minutes)} min",
    }


def _build_patient_queue_payload(patient):
    active_queue = list(_get_active_queue_queryset())
    # Pre-index active_queue for faster lookup
    active_map = {submission.id: index for index, submission in enumerate(active_queue, start=1)}
    
    patient_active_submissions = [sub for sub in active_queue if sub.patient_id == patient.id]
    
    current_submission = patient_active_submissions[0] if patient_active_submissions else PatientSubmission.objects.filter(patient=patient).order_by("-created_at").first()
    if not current_submission:
        return {
            "current_submission": None,
            "queue": {
                "position": None,
                "total_active_cases": len(active_queue),
                "ahead_of_you": 0,
                "behind_you": 0,
                "queue_state": "idle",
                "queue_state_label": "No active submission",
                "last_updated": None,
                "progress_percent": 0,
                "steps": _build_queue_steps(PatientSubmission.Status.COMPLETED)["steps"],
            },
            "message": "No active queue item found",
        }

    queue_position = active_map.get(current_submission.id)
    status_summary = _build_queue_steps(current_submission.status)
    wait_time_minutes = calculate_wait_time(current_submission)
    estimated_wait_range = _estimate_wait_range_minutes(current_submission, queue_position, len(active_queue))

    current_submission_payload = {
        "id": current_submission.id,
        "symptoms": current_submission.symptoms,
        "priority": current_submission.priority,
        "urgency_score": current_submission.urgency_score,
        "condition": current_submission.condition,
        "category": current_submission.category or "General",
        "status": current_submission.status,
        "queue_position": queue_position,
        "wait_time_minutes": wait_time_minutes,
        "sla_status": get_sla_status(wait_time_minutes),
        "estimated_wait_range": estimated_wait_range,
        "created_at": current_submission.created_at.isoformat(),
        "processed_at": current_submission.processed_at.isoformat() if current_submission.processed_at else None,
    }

    if queue_position is None:
        queue_summary = {
            "position": None,
            "total_active_cases": len(active_queue),
            "ahead_of_you": 0,
            "behind_you": 0,
            "queue_state": current_submission.status,
            "queue_state_label": "Completed" if current_submission.status == PatientSubmission.Status.COMPLETED else "No active queue position",
            "last_updated": current_submission.processed_at.isoformat() if current_submission.processed_at else current_submission.created_at.isoformat(),
            "progress_percent": status_summary["progress_percent"],
            "current_step": status_summary["current_step"],
            "estimated_wait_range": estimated_wait_range,
            "steps": status_summary["steps"],
        }
    else:
        queue_summary = {
            "position": queue_position,
            "total_active_cases": len(active_queue),
            "ahead_of_you": queue_position - 1,
            "behind_you": max(len(active_queue) - queue_position, 0),
            "queue_state": current_submission.status,
            "queue_state_label": status_summary["status_label"],
            "last_updated": current_submission.processed_at.isoformat() if current_submission.processed_at else current_submission.created_at.isoformat(),
            "progress_percent": status_summary["progress_percent"],
            "current_step": status_summary["current_step"],
            "estimated_wait_range": estimated_wait_range,
            "steps": status_summary["steps"],
        }

    return {
        "current_submission": current_submission_payload,
        "queue": queue_summary,
        "message": "Active queue found" if queue_position is not None else "Latest submission loaded",
    }


class PatientProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsPatient]
    serializer_class = GenericProfileSerializer

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
        
        api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")
        profile_photo_url = None
        if getattr(patient, "profile_photo", None):
            relative_url = patient.profile_photo.url
            profile_photo_url = f"{api_base_url}{relative_url}" if api_base_url else request.build_absolute_uri(relative_url)
            
        return Response({
            "id": patient.id,
            "name": patient.name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "contact_info": patient.contact_info,
            "user_id": patient.user.id,
            "username": patient.user.username,
            "email": patient.user.email,
            "profile_photo": profile_photo_url,
            "profile_photo_name": getattr(patient, "profile_photo_name", None),
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        request=GenericProfileSerializer,
        responses={200: GenericProfileSerializer, 400: ErrorResponseSerializer},
        description="Update authenticated patient's profile."
    )
    def patch(self, request):
        """Update authenticated patient's profile."""
        patient = self.get_or_create_patient(request.user)
        
        # Track if we need to save at the end
        needs_save = False
        
        # Update allowed fields
        if 'name' in request.data:
            patient.name = request.data['name']
            needs_save = True
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
            needs_save = True
        if 'contact_info' in request.data:
            patient.contact_info = request.data['contact_info']
            needs_save = True

        # Handle optional profile photo upload (multipart/form-data)
        if 'profile_photo' in request.FILES:
            uploaded = request.FILES['profile_photo']
            
            # Validate the uploaded photo
            try:
                validate_profile_photo(uploaded)
            except ValidationError as e:
                return Response({
                    "error": str(e.message) if hasattr(e, 'message') else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            patient.profile_photo = uploaded
            patient.profile_photo_name = getattr(uploaded, 'name', None)
            needs_save = True

        # Allow clients to remove profile photo by sending explicit null
        if request.data.get('remove_profile_photo') in [True, 'true', '1', 1]:
            logger.info(f"Removing profile photo for patient {patient.id}, current photo: {patient.profile_photo}")
            # Delete the file manually before clearing the field
            if patient.profile_photo:
                try:
                    patient.profile_photo.delete(save=False)
                    logger.info(f"Deleted file: {patient.profile_photo.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete profile photo file: {e}")
            # Use update() to bypass any caching issues
            Patient.objects.filter(pk=patient.pk).update(
                profile_photo='',
                profile_photo_name=None
            )
            # Refresh the instance to reflect the changes
            patient.refresh_from_db()
            logger.info(f"After update, profile_photo: {patient.profile_photo}")
        elif needs_save:
            # Only save if we haven't already saved
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


class PatientHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated, IsPatient]
    pagination_class = StandardResultsSetPagination
    serializer_class = PatientSubmissionSerializer

    def get_queryset(self):
        try:
            patient = self.request.user.patient_profile
        except Patient.DoesNotExist:
            return PatientSubmission.objects.none()
        
        return PatientSubmission.objects.filter(patient=patient).order_by('-created_at')


class PatientSubmissionDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSubmissionSerializer
    queryset = PatientSubmission.objects.all()
    lookup_url_kwarg = 'submission_id'

    def get(self, request, submission_id):
        """Get specific submission details."""
        try:
            submission = PatientSubmission.objects.get(id=submission_id)
            
            # Authorization check:
            # Patients can only see their own submissions
            if request.user.role == 'patient':
                try:
                    patient = request.user.patient_profile
                    if submission.patient != patient:
                        return error_response(code="ACCESS_DENIED", status_code=403, message="Forbidden")
                except Patient.DoesNotExist:
                    return error_response(code="PROFILE_MISSING", status_code=403, message="Patient profile missing")
            
            # Staff (Admin/Doctor/Nurse) can see any submission
            elif request.user.role not in ['admin', 'doctor', 'nurse', 'staff']:
                return error_response(code="ACCESS_DENIED", status_code=403, message="Unauthorized role")
                
        except PatientSubmission.DoesNotExist:
            return not_found_response("Submission not found")
        
        # Use PatientSubmissionSerializer for enriched data (demographics + AI)
        serializer = PatientSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientCurrentSessionView(GenericAPIView):
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

        payload = _build_patient_queue_payload(patient)
        return Response(payload, status=status.HTTP_200_OK)


class PatientQueueView(GenericAPIView):
    """
    Patient queue endpoint.

    GET /api/v1/patients/queue/ - Get the patient's current queue position and simplified progress tracker
    """
    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response({
                "current_submission": None,
                "queue": {
                    "position": None,
                    "total_active_cases": 0,
                    "ahead_of_you": 0,
                    "behind_you": 0,
                    "queue_state": "idle",
                    "queue_state_label": "No active submission",
                    "last_updated": None,
                    "progress_percent": 0,
                    "steps": _build_queue_steps(PatientSubmission.Status.COMPLETED)["steps"],
                },
                "message": "Patient profile not found"
            }, status=status.HTTP_200_OK)

        payload = _build_patient_queue_payload(patient)
        return Response(payload, status=status.HTTP_200_OK)




class TriageSubmissionsHistoryView(ListAPIView):
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


class ProfilePhotoUploadView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsPatient]
    
    def post(self, request):
        """Upload or replace profile photo."""
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return error_response(
                code="PROFILE_MISSING",
                status_code=404,
                message="Patient profile not found"
            )
        
        # Check if profile_photo file is in request
        if 'profile_photo' not in request.FILES:
            return Response({
                "error": "No profile_photo file provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['profile_photo']
        
        # Validate the uploaded photo
        try:
            validate_profile_photo(uploaded_file)
        except ValidationError as e:
            return Response({
                "error": str(e.message) if hasattr(e, 'message') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete old photo if exists
        if patient.profile_photo:
            try:
                patient.profile_photo.delete(save=False)
                logger.info(f"Deleted old profile photo for patient {patient.id}")
            except Exception as e:
                logger.warning(f"Failed to delete old profile photo: {e}")
        
        # Save new photo
        patient.profile_photo = uploaded_file
        patient.profile_photo_name = uploaded_file.name
        patient.save()
        
        logger.info(f"Uploaded profile photo for patient {patient.id}")
        
        api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")
        relative_url = patient.profile_photo.url
        profile_photo_url = f"{api_base_url}{relative_url}" if api_base_url else request.build_absolute_uri(relative_url)
        
        return Response({
            "message": "Profile photo uploaded successfully",
            "profile_photo": profile_photo_url,
            "profile_photo_name": patient.profile_photo_name
        }, status=status.HTTP_200_OK)


class ProfilePhotoDeleteView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsPatient]
    
    def delete(self, request):
        """Delete profile photo."""
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return error_response(
                code="PROFILE_MISSING",
                status_code=404,
                message="Patient profile not found"
            )
        
        # Check if patient has a profile photo
        if not patient.profile_photo:
            return Response({
                "error": "No profile photo to delete."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the photo file
        try:
            patient.profile_photo.delete(save=False)
            logger.info(f"Deleted profile photo file for patient {patient.id}")
        except Exception as e:
            logger.error(f"Failed to delete profile photo file: {e}")
            # Continue anyway to clear the database fields
        
        # Clear the database fields
        patient.profile_photo = None
        patient.profile_photo_name = None
        patient.save()
        
        logger.info(f"Cleared profile photo fields for patient {patient.id}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
