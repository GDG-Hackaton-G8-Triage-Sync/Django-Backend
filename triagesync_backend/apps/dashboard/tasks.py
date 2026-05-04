"""
Dashboard Background Tasks

This module provides Celery tasks for periodic background operations
related to the dashboard, including wait time updates and SLA monitoring.

Requirements: 14.1, 14.2, 14.3, 7.1, 7.2
"""

from celery import shared_task
from django.utils import timezone
import logging

from triagesync_backend.apps.patients.models import PatientSubmission
from .services.wait_time_service import (
    calculate_wait_time,
    get_sla_status,
    check_and_alert_sla_breach,
)
from triagesync_backend.apps.realtime.services.broadcast_service import (
    broadcast_wait_time_update,
    broadcast_queue_snapshot,
)

logger = logging.getLogger("dashboard.tasks")


@shared_task
def update_wait_times():
    """
    Periodic task to update wait times for active submissions.
    
    This task:
    1. Queries all active submissions (status = waiting/in_progress)
    2. Calculates current wait time for each submission
    3. Broadcasts wait time update via WebSocket
    4. Checks for SLA breaches and triggers alerts
    
    Configured to run every 60 seconds via Celery Beat.
    
    Requirements: 14.1, 14.2, 14.3, 7.1, 7.2
    """
    logger.info("Starting wait time update task")
    
    try:
        # Query all active submissions
        active_submissions = PatientSubmission.objects.filter(
            status__in=["waiting", "in_progress"]
        )
        
        submission_count = active_submissions.count()
        logger.info(f"Processing {submission_count} active submissions")
        
        # Process each submission
        for submission in active_submissions:
            try:
                # Calculate current wait time
                wait_time = calculate_wait_time(submission)
                sla_status = get_sla_status(wait_time)
                
                # Broadcast wait time update via WebSocket
                broadcast_wait_time_update(submission.id, wait_time, sla_status)
                # Periodically push queue snapshot so patient clients can reconcile position
                try:
                    broadcast_queue_snapshot(submission.id)
                except Exception:
                    logger.debug(f"Failed to broadcast queue snapshot for submission {submission.id}")
                
                # Check for SLA breaches and trigger alerts
                check_and_alert_sla_breach(submission)
                
            except Exception as e:
                # Log error for individual submission but continue processing others
                logger.error(
                    f"Error processing submission {submission.id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"Wait time update task completed successfully. "
            f"Processed {submission_count} submissions."
        )
        
    except Exception as e:
        # Log critical error if the entire task fails
        logger.error(
            f"Wait time update task failed: {e}",
            exc_info=True
        )
        raise
