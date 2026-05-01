from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from triagesync_backend.apps.authentication.models import User
from .models import Patient, PatientSubmission, StaffNote, VitalsLog

class ClinicalWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.nurse = User.objects.create_user(
            username='nurse_test',
            email='nurse@test.com',
            password='password123',
            role='nurse'
        )
        self.patient_user = User.objects.create_user(
            username='patient_test',
            email='patient@test.com',
            password='password123',
            role='patient'
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name='Test Patient'
        )
        self.submission = PatientSubmission.objects.create(
            patient=self.patient,
            symptoms='Chest pain'
        )
        self.client.force_authenticate(user=self.nurse)

    def test_clinical_verification(self):
        url = reverse('clinical-verify', kwargs={'submission_id': self.submission.id})
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.verified_by_user, self.nurse)
        self.assertIsNotNone(self.submission.verified_at)

    def test_staff_assignment(self):
        url = reverse('staff-assign', kwargs={'submission_id': self.submission.id})
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.assigned_to, self.nurse)
        self.assertEqual(self.submission.status, 'in_progress')

    def test_staff_notes(self):
        url = reverse('staff-notes', kwargs={'submission_id': self.submission.id})
        # Post a note
        response = self.client.post(url, {'content': 'Patient looks stable', 'is_internal': True})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get notes (as nurse)
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        
        # Get notes (as patient)
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0) # Internal note hidden

    def test_vitals_history(self):
        url = reverse('vitals-log', kwargs={'submission_id': self.submission.id})
        response = self.client.post(url, {
            'heart_rate': 80,
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'temperature_c': 36.6
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        url_history = reverse('vitals-history', kwargs={'submission_id': self.submission.id})
        response = self.client.get(url_history)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['temperature_c']), 36.6)
