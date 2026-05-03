from django.urls import path
from .views import (
    AdminUserListView, AdminUserRoleUpdateView, AdminSubmissionDeleteView, 
    AdminUserDeleteView, AuditLogListView, AdminUserSuspendView, 
    SystemConfigView, AdminReportExportView
)

urlpatterns = [
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:user_id>/', AdminUserDeleteView.as_view(), name='admin-user-delete'),
    path('users/<int:user_id>/role/', AdminUserRoleUpdateView.as_view(), name='admin-role-update'),
    path('users/<int:user_id>/suspend/', AdminUserSuspendView.as_view(), name='admin-user-suspend'),
    path('audit-logs/', AuditLogListView.as_view(), name='admin-audit-logs'),
    path('config/sla/', SystemConfigView.as_view(), name='admin-config'),
    path('reports/export/', AdminReportExportView.as_view(), name='admin-report-export'),
    path('patient/<int:submission_id>/', AdminSubmissionDeleteView.as_view(), name='admin-submission-delete'),
]



