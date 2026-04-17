"""
Custom middleware for TriageSync Backend
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(MiddlewareMixin):
    """
    Global exception handler middleware
    Catches unhandled exceptions and returns standardized error responses
    """
    def process_exception(self, request, exception):
        """
        Handle exceptions that weren't caught by views
        """
        logger.error(f"Unhandled exception: {str(exception)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(exception) if request.user.is_staff else 'An unexpected error occurred'
        }, status=500)
