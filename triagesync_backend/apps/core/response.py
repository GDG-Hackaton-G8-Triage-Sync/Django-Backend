from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    response_data = {}

    if message:
        response_data['message'] = message

    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data['data'] = data
    return Response(response_data, status=status_code)


def error_response(error, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    response_data = {'error': error}

    if details:
        response_data['details'] = details

    return Response(response_data, status=status_code)


def created_response(data, message=None):
    return success_response(data, message, status.HTTP_201_CREATED)


def unauthorized_response(error="Unauthorized access"):
    return error_response(error, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(error="Permission denied"):
    return error_response(error, status_code=status.HTTP_403_FORBIDDEN)


def not_found_response(error="Resource not found"):
    return error_response(error, status_code=status.HTTP_404_NOT_FOUND)


def validation_error_response(error="Invalid input", details=None):
    return error_response(error, details, status.HTTP_400_BAD_REQUEST)


def server_error_response(error="Internal server error"):
    return error_response(error, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
