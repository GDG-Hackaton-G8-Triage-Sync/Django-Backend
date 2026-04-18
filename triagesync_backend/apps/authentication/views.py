from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer
from .services.auth_service import get_tokens_for_user
from apps.core.response import success_response, error_response

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = get_tokens_for_user(user)

        return Response({
            "user": serializer.data,
            "tokens": tokens
        })


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data
        tokens = get_tokens_for_user(user)

        return Response({
            "tokens": tokens
        })
