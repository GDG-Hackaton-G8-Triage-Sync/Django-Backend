from django.urls import path
from .views import RegisterView, LoginView, RefreshTokenView, GenericProfileView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('profile/', GenericProfileView.as_view(), name='generic-profile'),
]
