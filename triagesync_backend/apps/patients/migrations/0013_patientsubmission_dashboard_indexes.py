from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0012_remove_photo_fields_from_submission"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="patientsubmission",
            index=models.Index(fields=["priority", "-urgency_score", "created_at"], name="patientsub_queue_idx"),
        ),
        migrations.AddIndex(
            model_name="patientsubmission",
            index=models.Index(fields=["status", "created_at"], name="patientsub_stat_created_idx"),
        ),
        migrations.AddIndex(
            model_name="patientsubmission",
            index=models.Index(fields=["category", "created_at"], name="patientsub_cat_cr_idx"),
        ),
        migrations.AddIndex(
            model_name="patientsubmission",
            index=models.Index(fields=["processed_at"], name="patientsub_processed_idx"),
        ),
    ]
