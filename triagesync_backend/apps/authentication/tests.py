"""
Authentication Tests - Registration with Required Fields

This test file covers:
1. Registration serializer validation
2. Required fields enforcement (age, gender, blood_type)
3. Blood type validation and normalization
4. Password confirmation validation
5. Patient profile creation
6. API endpoint integration
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from triagesync_backend.apps.patients.models import Patient

from triagesync_backend.apps.authentication.serializers import (
    RegisterSerializer,
    LoginSerializer,
    GenericProfileSerializer,
)

User = get_user_model()


# ============================================================================
# Registration Serializer Tests
# ============================================================================

class RegisterSerializerValidationTests(TestCase):
    """Test RegisterSerializer validation logic"""

    def test_valid_registration_minimal_required_fields(self):
        """Test registration with only required fields"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Verify all required fields are present
        validated = serializer.validated_data
        self.assertEqual(validated['name'], 'John Doe')
        self.assertEqual(validated['age'], 35)
        self.assertEqual(validated['gender'], 'male')
        self.assertEqual(validated['blood_type'], 'A+')

    def test_valid_registration_with_optional_fields(self):
        """Test registration with optional profile fields"""
        data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 28,
            'gender': 'female',
            'blood_type': 'O-',
            'health_history': 'No chronic conditions',
            'allergies': 'Penicillin',
            'current_medications': 'None',
            'bad_habits': 'None'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Verify optional fields are included
        validated = serializer.validated_data
        self.assertEqual(validated['health_history'], 'No chronic conditions')
        self.assertEqual(validated['allergies'], 'Penicillin')

    def test_registration_missing_name(self):
        """Test registration fails without name"""
        data = {
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_registration_missing_email(self):
        """Test registration fails without email"""
        data = {
            'name': 'John Doe',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_registration_missing_password(self):
        """Test registration fails without password"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_registration_missing_password2(self):
        """Test registration fails without password2"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password2', serializer.errors)

    def test_registration_missing_role(self):
        """Test registration fails without role"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('role', serializer.errors)

    def test_registration_missing_age(self):
        """Test registration fails without age"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)

    def test_registration_missing_gender(self):
        """Test registration fails without gender"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('gender', serializer.errors)

    def test_registration_missing_blood_type(self):
        """Test registration fails without blood_type"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('blood_type', serializer.errors)


# ============================================================================
# Password Validation Tests
# ============================================================================

class PasswordValidationTests(TestCase):
    """Test password confirmation validation"""

    def test_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'DifferentPassword456!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password2', serializer.errors)
        self.assertIn('do not match', str(serializer.errors['password2']).lower())

    def test_password_match(self):
        """Test registration succeeds when passwords match"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ============================================================================
# Blood Type Validation Tests
# ============================================================================

class BloodTypeValidationTests(TestCase):
    """Test blood type validation and normalization"""

    def test_valid_blood_types_standard_format(self):
        """Test all 8 valid blood types in standard format"""
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        
        for blood_type in blood_types:
            data = {
                'name': 'John Doe',
                'email': f'john{blood_type}@example.com',
                'password': 'SecurePassword123!',
                'password2': 'SecurePassword123!',
                'role': 'patient',
                'age': 35,
                'gender': 'male',
                'blood_type': blood_type
            }
            
            serializer = RegisterSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for {blood_type}: {serializer.errors}")
            self.assertEqual(serializer.validated_data['blood_type'], blood_type)

    def test_blood_type_normalization_lowercase(self):
        """Test blood type normalization from lowercase"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'a+'  # lowercase
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['blood_type'], 'A+')

    def test_blood_type_normalization_positive_word(self):
        """Test blood type normalization from 'positive' word"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'O positive'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['blood_type'], 'O+')

    def test_blood_type_normalization_negative_word(self):
        """Test blood type normalization from 'negative' word"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'AB negative'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['blood_type'], 'AB-')

    def test_blood_type_normalization_pos_abbreviation(self):
        """Test blood type normalization from 'pos' abbreviation"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'b pos'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['blood_type'], 'B+')

    def test_invalid_blood_type_c_plus(self):
        """Test invalid blood type C+"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'C+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('blood_type', serializer.errors)


class PatientProfilePhotoTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profilepatient',
            email='profile@example.com',
            password='testpass123',
            role='patient',
        )
        self.patient = Patient.objects.create(user=self.user, name='Profile Patient', age=31, gender='male', blood_type='O+')
        self.client.force_authenticate(user=self.user)

    def test_profile_patch_accepts_optional_photo(self):
        photo = SimpleUploadedFile('avatar.png', b'fake-image-bytes', content_type='image/png')

        response = self.client.patch(
            reverse('profile'),
            {'profile_photo': photo, 'contact_info': 'Updated contact'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.profile_photo)
        self.assertEqual(self.patient.profile_photo_name, 'avatar.png')
        self.assertIn('profile_photo', response.data)

    def test_profile_patch_can_remove_photo(self):
        self.patient.profile_photo_name = 'old.png'
        self.patient.save(update_fields=['profile_photo_name'])

        response = self.client.patch(
            reverse('profile'),
            {'remove_profile_photo': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.profile_photo)
        self.assertIsNone(self.patient.profile_photo_name)

    def test_profile_patch_allows_optional_fields_to_be_left_empty(self):
        self.patient.health_history = 'history'
        self.patient.allergies = 'allergies'
        self.patient.current_medications = 'meds'
        self.patient.bad_habits = 'habits'
        self.patient.save()

        response = self.client.patch(
            reverse('profile'),
            {
                'health_history': '',
                'allergies': '',
                'current_medications': '',
                'bad_habits': '',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.health_history, '')
        self.assertEqual(self.patient.allergies, '')
        self.assertEqual(self.patient.current_medications, '')
        self.assertEqual(self.patient.bad_habits, '')
        self.assertEqual(response.data['health_history'], '')
        self.assertEqual(response.data['allergies'], '')

    def test_invalid_blood_type_missing_rh(self):
        """Test invalid blood type without Rh factor"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A'  # Missing Rh
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('blood_type', serializer.errors)

    def test_invalid_blood_type_random_string(self):
        """Test invalid blood type with random string"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'XYZ123'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('blood_type', serializer.errors)


# ============================================================================
# Age Validation Tests
# ============================================================================

class AgeValidationTests(TestCase):
    """Test age validation"""

    def test_valid_age_zero(self):
        """Test age 0 is valid (newborn)"""
        data = {
            'name': 'Baby Doe',
            'email': 'baby@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 0,
            'gender': 'male',
            'blood_type': 'O+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_age_150(self):
        """Test age 150 is valid (maximum)"""
        data = {
            'name': 'Elder Doe',
            'email': 'elder@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 150,
            'gender': 'female',
            'blood_type': 'A-'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_age_negative(self):
        """Test negative age is invalid"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': -1,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)

    def test_invalid_age_over_150(self):
        """Test age over 150 is invalid"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 151,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)


# ============================================================================
# API Integration Tests
# ============================================================================

class RegistrationAPIIntegrationTests(APITestCase):
    """Test registration API endpoint"""

    def test_successful_registration(self):
        """Test successful registration returns tokens"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['role'], 'patient')

    def test_registration_creates_patient_profile(self):
        """Test registration creates patient profile with demographics"""
        data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 28,
            'gender': 'female',
            'blood_type': 'O-'
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(email='jane@example.com')
        self.assertEqual(user.username, 'Jane Smith')
        self.assertEqual(user.role, 'patient')
        
        # Verify patient profile was created with demographics
        from triagesync_backend.apps.patients.models import Patient
        patient = Patient.objects.get(user=user)
        self.assertEqual(patient.age, 28)
        self.assertEqual(patient.gender, 'female')
        self.assertEqual(patient.blood_type, 'O-')

    def test_registration_with_optional_fields_creates_full_profile(self):
        """Test registration with optional fields creates complete profile"""
        data = {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 42,
            'gender': 'male',
            'blood_type': 'B+',
            'health_history': 'Hypertension',
            'allergies': 'Penicillin',
            'current_medications': 'Lisinopril 10mg daily',
            'bad_habits': 'Smoking'
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify patient profile includes optional fields
        user = User.objects.get(email='bob@example.com')
        from triagesync_backend.apps.patients.models import Patient
        patient = Patient.objects.get(user=user)
        self.assertEqual(patient.health_history, 'Hypertension')
        self.assertEqual(patient.allergies, 'Penicillin')
        self.assertEqual(patient.current_medications, 'Lisinopril 10mg daily')
        self.assertEqual(patient.bad_habits, 'Smoking')

    def test_registration_missing_required_fields_returns_400(self):
        """Test registration without required fields returns 400"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35
            # Missing: gender, blood_type
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
        self.assertIn('gender', response.data['details'])
        self.assertIn('blood_type', response.data['details'])

    def test_registration_invalid_blood_type_returns_400(self):
        """Test registration with invalid blood type returns 400"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'SecurePassword123!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'invalid'
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
        self.assertIn('blood_type', response.data['details'])
        self.assertIn('Invalid blood type', str(response.data['details']['blood_type']))

    def test_registration_password_mismatch_returns_400(self):
        """Test registration with password mismatch returns 400"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123!',
            'password2': 'DifferentPassword456!',
            'role': 'patient',
            'age': 35,
            'gender': 'male',
            'blood_type': 'A+'
        }
        
        response = self.client.post('/api/v1/auth/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
        self.assertIn('password2', response.data['details'])


class LoginAPIIntegrationTests(APITestCase):
    """Test login API endpoint"""

    def test_successful_login_returns_tokens(self):
        user = User.objects.create_user(
            username='login-user',
            email='login-user@example.com',
            password='SecurePassword123!',
            role='patient',
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'login-user', 'password': 'SecurePassword123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertEqual(response.data['user_id'], user.id)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['role'], user.role)

    def test_invalid_login_returns_401(self):
        User.objects.create_user(
            username='login-user-2',
            email='login-user-2@example.com',
            password='SecurePassword123!',
            role='patient',
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': 'login-user-2', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('code', response.data)
        self.assertEqual(response.data['code'], 'AUTHENTICATION_FAILED')


if __name__ == '__main__':
    import unittest
    unittest.main()
