from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.db import transaction

from .serializers import RegisterSerializer, LoginSerializer, GenericProfileSerializer
from .services.auth_service import get_tokens_for_user
from triagesync_backend.apps.core.response import error_response
from triagesync_backend.apps.patients.models import Patient
from triagesync_backend.apps.notifications.services.notification_service import NotificationService


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return API information for GET requests."""
        return Response({
            "endpoint": "/api/v1/auth/register/",
            "method": "POST",
            "description": "Register a new user account",
            "required_fields": {
                "patient": ["name", "email", "password", "role", "age", "gender"],
                "staff": ["name", "email", "password", "role"]
            },
            "optional_fields": {
                "patient": ["blood_type", "health_history", "allergies", "current_medications", "bad_habits", "date_of_birth", "contact_info"],
                "staff": []
            },
            "example_request": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "role": "patient",
                "age": 30,
                "gender": "male",
                "blood_type": "A+"
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            # If patient role, highlight missing demographic fields
            missing_fields = []
            if request.data.get('role') == 'patient':
                # Required at registration for patient role
                for field in ['name', 'email', 'password', 'role', 'age']:
                    if not request.data.get(field) and request.data.get(field) != 0:
                        missing_fields.append(field)
            details = serializer.errors
            # Ensure blood_type/gender are surfaced when missing for patient role
            if request.data.get('role') == 'patient':
                for f in ('gender', 'blood_type'):
                    if f not in details and not request.data.get(f):
                        details[f] = ["This field is required."]
            if missing_fields:
                details['demographics'] = f"Missing required demographic fields: {', '.join(missing_fields)}"
            return error_response(
                code="VALIDATION_ERROR",
                message="Invalid registration data",
                details=details,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        # Send welcome notification to new user
        try:
            welcome_message = f"Welcome to TriageSync! Your {user.role} account has been successfully created."
            if user.role == 'patient':
                welcome_message += " You can now submit triage requests and track your medical status."
            else:
                welcome_message += " You can now access the staff dashboard and manage patient cases."
            
            NotificationService.create_notification(
                user=user,
                notification_type="system_message",
                title="Welcome to TriageSync",
                message=welcome_message,
                metadata={
                    "user_role": user.role,
                    "registration_date": user.date_joined.isoformat(),
                    "action_type": "user_registration"
                }
            )
        except Exception:
            # Don't fail registration if notification fails
            pass

        # Return direct flat structure per API contract Section 2.1
        return Response({
            "access_token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "role": user.role,
            "user_id": user.id,
            "name": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                code="AUTHENTICATION_FAILED",
                message="Invalid username or password",
                details={},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data
        tokens = get_tokens_for_user(user)

        # Return direct flat structure per API contract
        return Response({
            "access_token": tokens['access'],
            "refresh_token": tokens['refresh'],
            "role": user.role,
            "user_id": user.id,
            "name": user.username,
            "email": user.email
        })


class RefreshTokenView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/
    Accepts refresh_token and returns new access_token
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """
        Override post method to wrap simplejwt's token refresh logic
        with standardized error handling.
        """
        # Check if refresh token is provided
        if 'refresh' not in request.data or not request.data.get('refresh'):
            return error_response(
                code="INVALID_TOKEN",
                message="Refresh token is required",
                details={},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Call parent's post method to leverage simplejwt's token refresh logic
            return super().post(request, *args, **kwargs)
        except InvalidToken as e:
            # Handle invalid or expired refresh tokens
            return error_response(
                code="INVALID_TOKEN",
                message="Invalid or expired refresh token",
                details={},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except TokenError as e:
            # Handle other token-related errors
            return error_response(
                code="INVALID_TOKEN",
                message="Token error occurred",
                details={},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # Handle any other unexpected errors
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred during token refresh",
                details={},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Clear session data on logout (e.g., filter preferences).
    
    Note: This is a JWT-based system, so token invalidation happens client-side.
    This endpoint only clears server-side session data.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Clear all session data on logout."""
        try:
            # Clear all session data including filter preferences
            request.session.flush()
            
            return Response({
                "message": "Logout successful. Session data cleared."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An error occurred during logout",
                details={},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenericProfileView(APIView):
    """
    Generic profile management endpoint for all user roles.
    
    GET /api/v1/profile/
    - For patients: Returns Patient model fields
    - For staff: Returns User model fields
    
    PATCH /api/v1/profile/
    - For patients: Updates Patient model fields
    - For staff: Updates User model fields (name, email only)
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.4, 2.1, 2.3, 2.5
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retrieve user profile based on role."""
        user = request.user
        
        try:
            if user.role == 'patient':
                # Return Patient model for patients
                patient = Patient.objects.get(user=user)
                
                return Response({
                    'id': patient.id,
                    'name': patient.name,
                    'email': user.email,
                    'role': user.role,
                    'date_of_birth': patient.date_of_birth,
                    'contact_info': patient.contact_info,
                    'gender': patient.gender,
                    'age': patient.age,
                    'blood_type': patient.blood_type,
                    'health_history': patient.health_history,
                    'allergies': patient.allergies,
                    'current_medications': patient.current_medications,
                    'bad_habits': patient.bad_habits,
                }, status=status.HTTP_200_OK)
            else:
                # Return User model for staff
                return Response({
                    'id': user.id,
                    'name': user.first_name,
                    'email': user.email,
                    'role': 'staff',  # Normalize nurse/doctor to 'staff'
                    'username': user.username,
                }, status=status.HTTP_200_OK)
                
        except Patient.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="Patient profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update user profile based on role."""
        serializer = GenericProfileSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Invalid input data",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        user = request.user
        
        try:
            with transaction.atomic():
                if user.role == 'patient':
                    # Update Patient model for patients
                    patient = Patient.objects.select_for_update().get(user=user)
                    
                    # Update all provided fields
                    for field, value in validated_data.items():
                        setattr(patient, field, value)
                    
                    patient.save()
                    
                    # Return updated profile
                    return Response({
                        'id': patient.id,
                        'name': patient.name,
                        'email': user.email,
                        'role': user.role,
                        'date_of_birth': patient.date_of_birth,
                        'contact_info': patient.contact_info,
                        'gender': patient.gender,
                        'age': patient.age,
                        'blood_type': patient.blood_type,
                        'health_history': patient.health_history,
                        'allergies': patient.allergies,
                        'current_medications': patient.current_medications,
                        'bad_habits': patient.bad_habits,
                    }, status=status.HTTP_200_OK)
                else:
                    # Update User model for staff (name, email only)
                    if 'name' in validated_data:
                        user.first_name = validated_data['name']
                    if 'email' in validated_data:
                        user.email = validated_data['email']
                    
                    user.save()
                    
                    # Return updated profile
                    return Response({
                        'id': user.id,
                        'name': user.first_name,
                        'email': user.email,
                        'role': user.role,
                        'username': user.username,
                    }, status=status.HTTP_200_OK)
                    
        except Patient.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="Patient profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
