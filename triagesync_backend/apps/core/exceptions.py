from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that maps authentication exceptions
    to standardized error codes.
    
    Maps:
    - AuthenticationFailed -> AUTHENTICATION_REQUIRED (unless it's a JWT error)
    - InvalidToken -> INVALID_TOKEN
    - TokenError (expired) -> TOKEN_EXPIRED
    - PermissionDenied -> PERMISSION_DENIED
    
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
        
        # Format response consistently
        response.data = {
            "code": error_code,
            "message": error_message
        }
    
    return response
