"""
Configuration package initialization.

This ensures that the Celery app is loaded when Django starts,
so that @shared_task decorators will use this app.
"""

try:
	from .celery import app as celery_app
except ImportError:
	celery_app = None

__all__ = ('celery_app',)
