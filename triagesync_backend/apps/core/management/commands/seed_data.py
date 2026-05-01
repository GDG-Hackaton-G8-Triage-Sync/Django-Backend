import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from triagesync_backend.apps.patients.models import Patient, PatientSubmission, StaffNote, VitalsLog
from triagesync_backend.apps.api_admin.models import SystemConfig, AuditLog
from triagesync_backend.apps.notifications.models import Notification, NotificationPreference

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with realistic demo data for testing every possible application case.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning up existing data...")
        # Order matters for deletion due to FKs
        Notification.objects.all().delete()
        NotificationPreference.objects.all().delete()
        AuditLog.objects.all().delete()
        StaffNote.objects.all().delete()
        VitalsLog.objects.all().delete()
        PatientSubmission.objects.all().delete()
        Patient.objects.all().delete()
        # Keep superusers if any, but delete demo ones
        User.objects.filter(username__endswith='_demo').delete()
        User.objects.filter(email__contains='triagesync.com').delete()
        User.objects.filter(email__contains='example.com').delete()

        self.stdout.write("Starting comprehensive database seed...")

        # 1. System Configs
        SystemConfig.objects.update_or_create(key='SLA_CRITICAL_MINS', defaults={'value': 10, 'description': 'Minutes before a critical priority patient breaches SLA'})
        SystemConfig.objects.update_or_create(key='AI_CONFIDENCE_THRESHOLD', defaults={'value': 85, 'description': 'Minimum AI confidence required to auto-route'})
        SystemConfig.objects.update_or_create(key='MAINTENANCE_MODE', defaults={'value': False, 'description': 'Global maintenance mode toggle'})

        # 2. Staff Accounts
        admin_user, _ = User.objects.get_or_create(username='admin_demo', email='admin@triagesync.com', defaults={'role': 'admin'})
        admin_user.set_password('demo1234')
        admin_user.save()

        doc_user, _ = User.objects.get_or_create(username='dr_smith_demo', email='dr.smith@triagesync.com', defaults={'role': 'doctor'})
        doc_user.set_password('demo1234')
        doc_user.save()

        nurse_user, _ = User.objects.get_or_create(username='nurse_jones_demo', email='nurse.jones@triagesync.com', defaults={'role': 'nurse'})
        nurse_user.set_password('demo1234')
        nurse_user.save()
        
        # 2b. Suspended User (to test restricted access)
        suspended_user, _ = User.objects.get_or_create(
            username='bad_actor_demo', 
            email='suspended@example.com', 
            defaults={
                'role': 'patient',
                'is_suspended': True,
                'suspension_reason': 'Violation of terms of service: multiple fraudulent triage submissions.'
            }
        )
        suspended_user.set_password('demo1234')
        suspended_user.save()

        # 3. Patient Accounts & Profiles
        patients_data = [
            {'username': 'john_doe_demo', 'email': 'john@example.com', 'name': 'John Doe', 'age': 45, 'gender': 'Male', 'blood_type': 'A+'},
            {'username': 'jane_doe_demo', 'email': 'jane@example.com', 'name': 'Jane Doe', 'age': 32, 'gender': 'Female', 'blood_type': 'O-'},
            {'username': 'bob_smith_demo', 'email': 'bob@example.com', 'name': 'Bob Smith', 'age': 67, 'gender': 'Male', 'blood_type': 'B+'},
            {'username': 'alice_w_demo', 'email': 'alice@example.com', 'name': 'Alice Williams', 'age': 22, 'gender': 'Female', 'blood_type': 'AB+'},
            {'username': 'charlie_b_demo', 'email': 'charlie@example.com', 'name': 'Charlie Brown', 'age': 8, 'gender': 'Male', 'blood_type': 'O+'},
        ]

        created_patients = []
        for p_data in patients_data:
            p_user, _ = User.objects.get_or_create(username=p_data['username'], email=p_data['email'], defaults={'role': 'patient'})
            p_user.set_password('demo1234')
            p_user.save()

            # Ensure notification preferences exist
            NotificationPreference.objects.get_or_create(user=p_user)

            patient, _ = Patient.objects.get_or_create(
                user=p_user,
                defaults={
                    'name': p_data['name'],
                    'age': p_data['age'],
                    'gender': p_data['gender'],
                    'blood_type': p_data['blood_type'],
                    'health_history': 'No major history' if random.random() > 0.5 else 'Hypertension',
                    'allergies': 'None' if random.random() > 0.5 else 'Penicillin'
                }
            )
            created_patients.append(patient)

        # 4. Patient Submissions (Triage Records - All Priority Levels 1-5)
        submissions_data = [
            # P1: Critical (In Progress)
            {
                'patient': created_patients[0], 'symptoms': 'Severe crushing chest pain radiating to left arm. Sweating and short of breath.',
                'condition': 'Acute Myocardial Infarction', 'priority': 1, 'urgency_score': 95, 'is_critical': True,
                'status': 'in_progress', 'assigned_to': doc_user, 'offset_mins': 5, 'category': 'Cardiac'
            },
            # P1: Critical (Completed)
            {
                'patient': created_patients[2], 'symptoms': 'Sudden weakness on right side, slurred speech. Started 30 mins ago.',
                'condition': 'Acute Ischemic Stroke', 'priority': 1, 'urgency_score': 98, 'is_critical': True,
                'status': 'completed', 'assigned_to': doc_user, 'verified_by': doc_user, 'offset_mins': 120, 'category': 'Neurological'
            },
            # P2: Emergent (Waiting)
            {
                'patient': created_patients[1], 'symptoms': 'Difficulty breathing, wheezing. Known asthmatic, inhaler not helping.',
                'condition': 'Acute Asthma Exacerbation', 'priority': 2, 'urgency_score': 75, 'is_critical': False,
                'status': 'waiting', 'assigned_to': None, 'offset_mins': 20, 'category': 'Respiratory'
            },
            # P3: Urgent (In Progress)
            {
                'patient': created_patients[4], 'symptoms': 'Fell off bike, deep laceration on right forearm. Bleeding is controlled.',
                'condition': 'Laceration', 'priority': 3, 'urgency_score': 55, 'is_critical': False,
                'status': 'in_progress', 'assigned_to': nurse_user, 'offset_mins': 30, 'category': 'Trauma'
            },
            # P4: Semi-Urgent (Waiting)
            {
                'patient': created_patients[3], 'symptoms': 'Fever of 102F, severe sore throat, painful swallowing for 2 days.',
                'condition': 'Streptococcal Pharyngitis', 'priority': 4, 'urgency_score': 35, 'is_critical': False,
                'status': 'waiting', 'assigned_to': None, 'offset_mins': 15, 'category': 'General'
            },
            # P5: Non-Urgent (Waiting)
            {
                'patient': created_patients[0], 'symptoms': 'Mild runny nose and itchy eyes for 3 days. Seasonal allergies suspected.',
                'condition': 'Allergic Rhinitis', 'priority': 5, 'urgency_score': 10, 'is_critical': False,
                'status': 'waiting', 'assigned_to': None, 'offset_mins': 60, 'category': 'General'
            },
        ]

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
                category=s_data.get('category', 'General'),
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
            
            # 5. Notifications
            if sub.priority <= 2:
                # Notify staff of critical/emergent case
                for staff in [doc_user, nurse_user, admin_user]:
                    Notification.objects.create(
                        user=staff,
                        notification_type=Notification.NotificationType.CRITICAL_ALERT,
                        title=f"Critical Alert: P{sub.priority} Case",
                        message=f"New P{sub.priority} submission (ID: {sub.id}) from {sub.patient.name}.",
                        metadata={'submission_id': sub.id, 'priority': sub.priority}
                    )
            
            # Notify patient of status
            Notification.objects.create(
                user=sub.patient.user,
                notification_type=Notification.NotificationType.TRIAGE_STATUS_CHANGE,
                title="Triage Update",
                message=f"Your triage status has been updated to {sub.status}.",
                metadata={'submission_id': sub.id, 'status': sub.status}
            )

        # 6. Audit Logs
        AuditLog.objects.create(
            actor=admin_user,
            action_type='USER_SUSPENDED',
            target_description=f"User {suspended_user.email}",
            justification="Policy violation reported by medical staff.",
            metadata={'user_id': suspended_user.id}
        )
        
        AuditLog.objects.create(
            actor=admin_user,
            action_type='SYSTEM_CONFIG_UPDATED',
            target_description="Updated SLA_CRITICAL_MINS",
            justification="Quarterly protocol review.",
            metadata={'key': 'SLA_CRITICAL_MINS', 'new_value': 10}
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with all possible application cases!"))
        self.stdout.write("-" * 50)
        self.stdout.write("AUTHENTICATION ACCOUNTS:")
        self.stdout.write(f"  Admin:      {admin_user.email} / demo1234")
        self.stdout.write(f"  Doctor:     {doc_user.email} / demo1234")
        self.stdout.write(f"  Nurse:      {nurse_user.email} / demo1234")
        self.stdout.write(f"  Patient:    john@example.com / demo1234")
        self.stdout.write(f"  Suspended:  suspended@example.com / demo1234")
        self.stdout.write("-" * 50)
        self.stdout.write("SCENARIOS SEEDED:")
        self.stdout.write("  - P1-P5 Triage cases (Waiting, In-Progress, Completed)")
        self.stdout.write("  - Vitals history and Staff clinical notes")
        self.stdout.write("  - Notifications (Staff alerts & Patient status updates)")
        self.stdout.write("  - Admin Audit Logs for security tracking")
        self.stdout.write("  - User suspension case for access control testing")
        self.stdout.write("-" * 50)
