from rest_framework.views import APIView
from rest_framework import status

from .serializers import RegisterSerializer, LoginSerializer
from .services.auth_service import get_tokens_for_user
from apps.core.response import success_response, error_response


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        return success_response({
            "user": serializer.data,
            "tokens": tokens
        })


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                {"message": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = serializer.validated_data
        tokens = get_tokens_for_user(user)

        return success_response({
            "tokens": tokens
        })
