from django.urls import path

from .views import (
    LoginView, RegisterView,
    AdminUserListView, AdminUserRoleUpdateView, AdminPatientDeleteView,
    RefreshTokenView, LogoutView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="token_logout"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:id>/role/", AdminUserRoleUpdateView.as_view(), name="admin-user-role-update"),
    path("admin/patient/<int:id>/", AdminPatientDeleteView.as_view(), name="admin-patient-delete"),
]
