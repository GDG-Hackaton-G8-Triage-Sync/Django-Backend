from django.urls import path

from triagesync_backend.apps.dashboard.views import AdminAnalyticsView, AdminOverviewView

from .views import (
    AdminSubmissionDeleteView,
    AdminUserDeleteView,
    AdminUserListView,
    AdminUserRoleUpdateView,
)


urlpatterns = [
    path("overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:user_id>/", AdminUserDeleteView.as_view(), name="admin-user-delete"),
    path("users/<int:user_id>/role/", AdminUserRoleUpdateView.as_view(), name="admin-role-update"),
    path("submissions/<int:submission_id>/", AdminSubmissionDeleteView.as_view(), name="admin-submission-delete"),
    path("patient/<int:submission_id>/", AdminSubmissionDeleteView.as_view(), name="admin-submission-delete-legacy"),
]
