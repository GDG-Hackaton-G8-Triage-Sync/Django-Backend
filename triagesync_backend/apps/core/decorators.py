"""
Decorators for common view patterns and error handling.
"""
from functools import wraps
from rest_framework import status
from .response import error_response, validation_error_response


def handle_common_errors(view_func):
    """
    Decorator to handle common view errors.
    
    Catches all exceptions and returns a standardized error response.
    Use this as the outermost decorator to catch any unhandled exceptions.
    
    Example:
        @handle_common_errors
        def patch(self, request, id):
            # Your view logic here
            pass
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return view_func(self, request, *args, **kwargs)
        except Exception as e:
            return error_response(
                code="INTERNAL_SERVER_ERROR",
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper


def validate_serializer(serializer_class):
    """
    Decorator to validate serializer before view execution.
    
    Validates the request data using the provided serializer class.
    If validation fails, returns a standardized validation error response.
    If validation succeeds, attaches validated_data to the request object.
    
    Args:
        serializer_class: The serializer class to use for validation
    
    Example:
        @validate_serializer(RoleUpdateSerializer)
        def patch(self, request, user_id):
            # Access validated data via request.validated_data
            role = request.validated_data['role']
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            serializer = serializer_class(data=request.data)
            if not serializer.is_valid():
                return validation_error_response(
                    error="Invalid input data",
                    details=serializer.errors
                )
            # Attach validated data to request for use in view
            request.validated_data = serializer.validated_data
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def handle_does_not_exist(model_name="Resource"):
    """
    Decorator to handle DoesNotExist exceptions for a specific model.
    
    Catches DoesNotExist exceptions and returns a standardized 404 response.
    
    Args:
        model_name: The name of the model for the error message (default: "Resource")
    
    Example:
        @handle_does_not_exist("User")
        def patch(self, request, user_id):
            user = User.objects.get(id=user_id)  # Will return 404 if not found
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            try:
                return view_func(self, request, *args, **kwargs)
            except Exception as e:
                if "DoesNotExist" in str(type(e).__name__):
                    return error_response(
                        code="NOT_FOUND",
                        message=f"{model_name} not found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                raise  # Re-raise if not a DoesNotExist exception
        return wrapper
    return decorator
