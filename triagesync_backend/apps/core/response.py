"""
Standard API response utilities
⚠️ Use this file (response.py) NOT responses.py
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Return direct data without envelope per API contract Section 2.3
    
    API contract requires direct JSON resources (no success envelopes)
    """
    return Response(data, status=status_code)


def error_response(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Return {code, message, details} format per API contract
    
    API contract requires error format: {"code": "...", "message": "...", "details": ...}
    """
    response_data = {"code": code, "message": message}
    if details is not None:
        response_data["details"] = details
    return Response(response_data, status=status_code)


def created_response(data, message=None):
    """
    Standard creation response (201)
    """
    return success_response(data, message, status.HTTP_201_CREATED)


def unauthorized_response(error="Unauthorized access"):
    """
    Standard 401 response
    """
    return error_response("UNAUTHORIZED", error, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(error="Permission denied"):
    """
    Standard 403 response
    """
    return error_response("FORBIDDEN", error, status_code=status.HTTP_403_FORBIDDEN)


def not_found_response(error="Resource not found"):
    """
    Standard 404 response
    """
    return error_response("NOT_FOUND", error, status_code=status.HTTP_404_NOT_FOUND)


def validation_error_response(error="Invalid input", details=None):
    """
    Standard validation error response (400)
    """
    return error_response("VALIDATION_ERROR", error, details, status.HTTP_400_BAD_REQUEST)


def server_error_response(error="Internal server error"):
    """
    Standard 500 response
    """
    return error_response("INTERNAL_SERVER_ERROR", error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
