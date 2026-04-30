# Generated migration for underutilized-features-implementation
# Task 1.5: Add routing and filtering fields to PatientSubmission

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0004_alter_patient_age_alter_patient_blood_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientsubmission',
            name='requires_immediate_attention',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='patientsubmission',
            name='specialist_referral_suggested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='patientsubmission',
            name='critical_keywords',
            field=models.JSONField(default=list, blank=True),
        ),
    ]
