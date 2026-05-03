from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    AuthenticationFailed, 
    PermissionDenied, 
    MethodNotAllowed,
    NotFound,
    ValidationError
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that maps exceptions
    to standardized error codes.
    
    Maps:
    - AuthenticationFailed -> AUTHENTICATION_REQUIRED (unless it's a JWT error)
    - InvalidToken -> INVALID_TOKEN
    - TokenError (expired) -> TOKEN_EXPIRED
    - PermissionDenied -> PERMISSION_DENIED
    - MethodNotAllowed -> METHOD_NOT_ALLOWED
    - NotFound -> NOT_FOUND
    - ValidationError -> VALIDATION_ERROR
    
    Requirements: 7.3, 7.4, 7.5
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_code = "INTERNAL_SERVER_ERROR"
        error_message = str(exc)
        
        # Map exception types to error codes
        if isinstance(exc, (InvalidToken, TokenError)):
            # Check if it's an expired token
            if "expired" in error_message.lower():
                error_code = "TOKEN_EXPIRED"
            else:
                error_code = "INVALID_TOKEN"
        elif isinstance(exc, AuthenticationFailed):
            # Check if it's a JWT-related authentication failure
            if "token" in error_message.lower() or "jwt" in error_message.lower():
                error_code = "INVALID_TOKEN"
            else:
                error_code = "AUTHENTICATION_REQUIRED"
        elif isinstance(exc, PermissionDenied):
            error_code = "PERMISSION_DENIED"
        elif isinstance(exc, MethodNotAllowed):
            error_code = "METHOD_NOT_ALLOWED"
            # Provide helpful message about allowed methods
            # Extract allowed methods from the exception
            # exc.detail is a list of ErrorDetail objects representing allowed methods
            allowed_methods = []
            if hasattr(exc, 'detail') and isinstance(exc.detail, list):
                # Extract string values from ErrorDetail objects
                allowed_methods = [str(method) for method in exc.detail]
            
            if allowed_methods:
                error_message = f"Method '{context['request'].method}' not allowed. Allowed methods: {', '.join(allowed_methods)}"
            else:
                error_message = f"Method '{context['request'].method}' not allowed."
        elif isinstance(exc, NotFound):
            error_code = "NOT_FOUND"
        elif isinstance(exc, ValidationError):
            error_code = "VALIDATION_ERROR"
        
        # Format response consistently
        response.data = {
            "code": error_code,
            "message": error_message
        }
    
    return response
