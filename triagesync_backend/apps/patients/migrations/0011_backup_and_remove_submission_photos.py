# Generated migration for profile photo migration
# This migration backs up existing PatientSubmission photo data and removes photo fields

import json
import os
from datetime import datetime
from django.db import migrations
from django.conf import settings


def backup_submission_photos(apps, schema_editor):
    """
    Backup existing PatientSubmission photo data to JSON file before removing fields.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    PatientSubmission = apps.get_model('patients', 'PatientSubmission')
    
    # Find all submissions with photos
    submissions_with_photos = PatientSubmission.objects.filter(
        photo__isnull=False
    ).exclude(photo='')
    
    count = submissions_with_photos.count()
    
    if count == 0:
        print("No PatientSubmission records with photos found. Skipping backup.")
        return
    
    # Prepare backup data
    backup_data = []
    submission_ids = []
    
    for submission in submissions_with_photos:
        backup_entry = {
            'submission_id': submission.id,
            'patient_id': submission.patient_id,
            'photo_path': submission.photo.name if submission.photo else None,
            'photo_name': submission.photo_name,
            'created_at': submission.created_at.isoformat() if submission.created_at else None,
        }
        backup_data.append(backup_entry)
        submission_ids.append(submission.id)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'triage_photos_backup_{timestamp}.json'
    
    # Determine backup file path (project root)
    # Go up from migrations directory to project root
    backup_path = os.path.join(settings.BASE_DIR, backup_filename)
    
    # Write backup file
    with open(backup_path, 'w') as f:
        json.dump({
            'backup_timestamp': timestamp,
            'total_count': count,
            'submission_ids': submission_ids,
            'data': backup_data
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"PHOTO BACKUP SUMMARY")
    print(f"{'='*60}")
    print(f"Total submissions with photos: {count}")
    print(f"Submission IDs: {submission_ids}")
    print(f"Backup file created: {backup_path}")
    print(f"{'='*60}\n")


def reverse_backup(apps, schema_editor):
    """
    Reverse migration - no action needed for backup.
    Photo data can be restored manually from backup file if needed.
    """
    print("Reverse migration: Photo backup cannot be automatically reversed.")
    print("If you need to restore photo data, use the backup JSON file.")


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0010_patient_profile_photo_patient_profile_photo_name'),
    ]

    operations = [
        # First, backup existing photo data
        migrations.RunPython(backup_submission_photos, reverse_backup),
        
        # Then remove the photo fields from PatientSubmission model
        migrations.RemoveField(
            model_name='patientsubmission',
            name='photo',
        ),
        migrations.RemoveField(
            model_name='patientsubmission',
            name='photo_name',
        ),
    ]
