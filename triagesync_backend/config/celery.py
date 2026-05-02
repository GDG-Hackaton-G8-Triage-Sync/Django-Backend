"""
Celery Configuration for TriageSync Backend

This module configures Celery for asynchronous task processing and
periodic task scheduling (Celery Beat).
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'triagesync_backend.config.settings')

app = Celery('triagesync_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Celery Beat Schedule - Periodic Tasks
app.conf.beat_schedule = {
    'update-wait-times-every-60-seconds': {
        'task': 'triagesync_backend.apps.dashboard.tasks.update_wait_times',
        'schedule': 60.0,  # Run every 60 seconds
        'options': {
            'expires': 55.0,  # Task expires after 55 seconds (before next run)
        }
    },
}

# Celery configuration
app.conf.update(
    # Task result backend (optional - stores task results)
    result_backend='redis://' if not os.getenv('REDIS_URL') else os.getenv('REDIS_URL'),
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery configuration"""
    print(f'Request: {self.request!r}')
