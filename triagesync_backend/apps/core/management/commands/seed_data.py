import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from triagesync_backend.apps.patients.models import Patient, PatientSubmission, StaffNote, VitalsLog
from triagesync_backend.apps.api_admin.models import SystemConfig

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with realistic demo data for presentation purposes.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seed...")

        # 1. System Configs
        SystemConfig.objects.get_or_create(key='SLA_CRITICAL_MINS', defaults={'value': 10, 'description': 'Minutes before a critical priority patient breaches SLA'})
        SystemConfig.objects.get_or_create(key='AI_CONFIDENCE_THRESHOLD', defaults={'value': 85, 'description': 'Minimum AI confidence required to auto-route'})

        # 2. Staff Accounts
        admin_user, _ = User.objects.get_or_create(username='admin_demo', email='admin@triagesync.com', defaults={'role': 'admin'})
        admin_user.set_password('demo1234')
        admin_user.save()

        doc_user, _ = User.objects.get_or_create(username='dr_smith', email='dr.smith@triagesync.com', defaults={'role': 'doctor'})
        doc_user.set_password('demo1234')
        doc_user.save()

        nurse_user, _ = User.objects.get_or_create(username='nurse_jones', email='nurse.jones@triagesync.com', defaults={'role': 'nurse'})
        nurse_user.set_password('demo1234')
        nurse_user.save()

        # 3. Patient Accounts & Profiles
        patients_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'name': 'John Doe', 'age': 45, 'gender': 'Male', 'blood_type': 'A+'},
            {'username': 'jane_doe', 'email': 'jane@example.com', 'name': 'Jane Doe', 'age': 32, 'gender': 'Female', 'blood_type': 'O-'},
            {'username': 'bob_smith', 'email': 'bob@example.com', 'name': 'Bob Smith', 'age': 67, 'gender': 'Male', 'blood_type': 'B+'},
            {'username': 'alice_w', 'email': 'alice@example.com', 'name': 'Alice Williams', 'age': 22, 'gender': 'Female', 'blood_type': 'AB+'},
            {'username': 'charlie_b', 'email': 'charlie@example.com', 'name': 'Charlie Brown', 'age': 8, 'gender': 'Male', 'blood_type': 'O+'},
        ]

        created_patients = []
        for p_data in patients_data:
            p_user, _ = User.objects.get_or_create(username=p_data['username'], email=p_data['email'], defaults={'role': 'patient'})
            p_user.set_password('demo1234')
            p_user.save()

            patient, _ = Patient.objects.get_or_create(
                user=p_user,
                defaults={
                    'name': p_data['name'],
                    'age': p_data['age'],
                    'gender': p_data['gender'],
                    'blood_type': p_data['blood_type']
                }
            )
            created_patients.append(patient)

        # 4. Patient Submissions (Triage Records)
        submissions_data = [
            {
                'patient': created_patients[0], 'symptoms': 'Severe crushing chest pain radiating to left arm. Sweating and short of breath.',
                'condition': 'Acute Myocardial Infarction', 'priority': 1, 'urgency_score': 95, 'is_critical': True,
                'status': 'in_progress', 'assigned_to': doc_user, 'offset_mins': 5
            },
            {
                'patient': created_patients[1], 'symptoms': 'Twisted ankle while running. Swollen and painful to bear weight.',
                'condition': 'Ankle Sprain', 'priority': 4, 'urgency_score': 30, 'is_critical': False,
                'status': 'waiting', 'assigned_to': None, 'offset_mins': 45
            },
            {
                'patient': created_patients[2], 'symptoms': 'Sudden weakness on right side, slurred speech. Started 30 mins ago.',
                'condition': 'Acute Ischemic Stroke', 'priority': 1, 'urgency_score': 98, 'is_critical': True,
                'status': 'completed', 'assigned_to': doc_user, 'verified_by': doc_user, 'offset_mins': 120
            },
            {
                'patient': created_patients[3], 'symptoms': 'Fever of 102F, severe sore throat, painful swallowing for 2 days.',
                'condition': 'Streptococcal Pharyngitis', 'priority': 4, 'urgency_score': 40, 'is_critical': False,
                'status': 'waiting', 'assigned_to': None, 'offset_mins': 15
            },
            {
                'patient': created_patients[4], 'symptoms': 'Fell off bike, deep laceration on right forearm. Bleeding is controlled.',
                'condition': 'Laceration', 'priority': 3, 'urgency_score': 60, 'is_critical': False,
                'status': 'in_progress', 'assigned_to': nurse_user, 'offset_mins': 30
            },
        ]

        PatientSubmission.objects.all().delete() # Clear old ones to prevent clutter
        
        now = timezone.now()
        
        for s_data in submissions_data:
            sub = PatientSubmission.objects.create(
                patient=s_data['patient'],
                symptoms=s_data['symptoms'],
                condition=s_data['condition'],
                priority=s_data['priority'],
                urgency_score=s_data['urgency_score'],
                is_critical=s_data['is_critical'],
                status=s_data['status'],
                assigned_to=s_data.get('assigned_to'),
                category='Cardiovascular' if s_data['priority'] == 1 else 'General',
                confidence=89.5,
                source='AI_MODEL'
            )
            
            # Backdate creation
            sub.created_at = now - timedelta(minutes=s_data['offset_mins'])
            if s_data.get('verified_by'):
                sub.verified_by_user = s_data['verified_by']
                sub.verified_at = sub.created_at + timedelta(minutes=10)
                sub.processed_at = sub.verified_at
            sub.save()

            # Add Vitals
            VitalsLog.objects.create(
                submission=sub,
                recorded_by=nurse_user,
                heart_rate=random.randint(60, 110),
                systolic_bp=random.randint(100, 160),
                diastolic_bp=random.randint(60, 100),
                temperature_c=round(random.uniform(36.5, 39.5), 1),
                oxygen_saturation=random.randint(92, 100)
            )

            # Add Staff Notes
            if sub.status != 'waiting':
                StaffNote.objects.create(
                    submission=sub,
                    author=nurse_user,
                    content="Patient vitals taken. Placed in room " + str(random.randint(1, 10)),
                    is_internal=True
                )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with realistic demo data!"))
        self.stdout.write("Test accounts:")
        self.stdout.write("  Admin:  admin@triagesync.com / demo1234")
        self.stdout.write("  Doctor: dr.smith@triagesync.com / demo1234")
        self.stdout.write("  Nurse:  nurse.jones@triagesync.com / demo1234")
        self.stdout.write("  Patient: john@example.com / demo1234")
