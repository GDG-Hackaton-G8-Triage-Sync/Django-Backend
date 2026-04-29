from django.urls import path
from .views import AdminUserListView, AdminUserRoleUpdateView, AdminSubmissionDeleteView

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:user_id>/role/', AdminUserRoleUpdateView.as_view(), name='admin-role-update'),
    path('patient/<int:submission_id>/', AdminSubmissionDeleteView.as_view(), name='admin-submission-delete'),
]
