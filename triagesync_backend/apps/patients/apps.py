from django.apps import AppConfig


class PatientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "triagesync_backend.apps.patients"

    def ready(self):
        """
        Import signal handlers when the app is ready.
        
        This ensures signals are registered exactly once when Django starts.
        Requirements: 10.1, 10.3
        """
        # Import signals module to register signal handlers
        from . import signals  # noqa: F401
