from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from triagesync_backend.apps.authentication.models import User
from .models import AuditLog, SystemConfig

class AdminPortalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123',
            role='admin'
        )
        self.nurse_user = User.objects.create_user(
            username='nurse',
            email='nurse@test.com',
            password='password123',
            role='nurse'
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_audit_log_creation(self):
        # Trigger an action that logs
        url = reverse('admin-role-update', kwargs={'user_id': self.nurse_user.id})
        response = self.client.patch(url, {'role': 'admin', 'justification': 'Promotion'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action_type='ROLE_UPDATE').exists())

    def test_audit_log_list(self):
        AuditLog.objects.create(
            actor=self.admin_user,
            action_type='TEST_ACTION',
            target_description='Test'
        )
        url = reverse('admin-audit-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_suspension(self):
        url = reverse('admin-user-suspend', kwargs={'user_id': self.nurse_user.id})
        response = self.client.patch(url, {'is_suspended': True, 'reason': 'Investigation'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.nurse_user.refresh_from_db()
        self.assertTrue(self.nurse_user.is_suspended)
        self.assertEqual(self.nurse_user.suspension_reason, 'Investigation')

    def test_system_config_update(self):
        url = reverse('admin-config')
        response = self.client.patch(url, {'key': 'SLA_CRITICAL_MINS', 'value': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        config = SystemConfig.objects.get(key='SLA_CRITICAL_MINS')
        self.assertEqual(config.value, 5)

    def test_report_export(self):
        url = reverse('admin-report-export')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
