from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

class AdminUserListView(APIView):
    def get(self, request):
        # Mock user list
        return Response([
            {"id": 1, "username": "admin", "role": "admin"},
            {"id": 2, "username": "staff1", "role": "staff"},
            {"id": 3, "username": "patient1", "role": "patient"},
        ])

class AdminUserRoleUpdateView(APIView):
    def patch(self, request, id):
        # Mock role update
        return Response({"id": id, "role": request.data.get("role", "staff")}, status=status.HTTP_200_OK)

class AdminPatientDeleteView(APIView):
    def delete(self, request, id):
        # Mock patient delete
        return Response({"id": id, "deleted": True}, status=status.HTTP_204_NO_CONTENT)

from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

# JWT Refresh endpoint
class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

# JWT Logout endpoint (blacklist refresh token)
class LogoutView(TokenBlacklistView):
    permission_classes = [AllowAny]
