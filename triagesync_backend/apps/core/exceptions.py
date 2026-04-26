"""
Custom exceptions and exception handler
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from .response import error_response


class TriageException(APIException):
    """Base exception for triage-related errors"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A triage error occurred.'
    default_code = 'triage_error'


class AIServiceException(TriageException):
    """Exception for AI service failures"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI service is currently unavailable.'
    default_code = 'ai_service_error'


class ValidationException(TriageException):
    """Exception for validation errors"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation failed.'
    default_code = 'validation_error'


class PermissionDeniedException(TriageException):
    """Exception for permission errors"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied.'
    default_code = 'permission_denied'


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize error response format
        error_data = {
            'error': response.data.get('detail', str(exc))
        }
        
        # Add additional error details if available
        if isinstance(response.data, dict):
            details = {k: v for k, v in response.data.items() if k != 'detail'}
            if details:
                error_data['details'] = details
        
        response.data = error_data
    
    return response
