from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0013_patientsubmission_dashboard_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patientsubmission",
            name="status",
            field=models.CharField(
                choices=[
                    ("waiting", "Waiting"),
                    ("in_progress", "In Progress"),
                    ("completed", "Completed"),
                    ("canceled", "Canceled"),
                ],
                default="waiting",
                max_length=20,
            ),
        ),
    ]
