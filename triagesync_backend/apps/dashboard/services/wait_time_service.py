"""
Wait Time Service Module

This module provides centralized functionality for wait time calculations,
SLA monitoring, and alert generation for patient submissions.

Requirements: 4.1, 4.2, 4.3, 4.4, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5,
              7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4,
              13.1, 13.2, 13.3, 13.4
"""

import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Max, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce, Now
from triagesync_backend.apps.patients.models import PatientSubmission

logger = logging.getLogger("dashboard.wait_time_service")


def calculate_wait_time(submission):
    """
    Calculate wait time in minutes for a submission.
    
    Args:
        submission: PatientSubmission instance
        
    Returns:
        Wait time in minutes (float with 1 decimal precision)
        
    Logic:
        - If status is 'completed' and processed_at exists: processed_at - created_at
        - If status is 'completed' but processed_at is null: current_time - created_at (with warning)
        - Otherwise: current_time - created_at
        
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    if submission.status == "completed":
        if submission.processed_at:
            end_time = submission.processed_at
        else:
            # Handle edge case: completed submission without processed_at
            end_time = timezone.now()
            logger.warning(
                f"Submission {submission.id} is completed but processed_at is null. "
                f"Using current time for wait time calculation."
            )
    else:
        # For waiting or in_progress submissions, use current time
        end_time = timezone.now()
    
    delta = end_time - submission.created_at
    wait_time_minutes = delta.total_seconds() / 60
    
    # Return with 1 decimal precision
    return round(wait_time_minutes, 1)


def get_sla_status(wait_time_minutes):
    """
    Determine SLA status based on wait time.
    
    Args:
        wait_time_minutes: Wait time in minutes (float)
        
    Returns:
        One of: 'normal', 'warning', 'critical'
        
    Logic:
        - wait_time < 25: 'normal'
        - 25 <= wait_time < 30: 'warning'
        - wait_time >= 30: 'critical'
        
    Requirements: 5.2, 5.3
    """
    if wait_time_minutes < 25:
        return 'normal'
    elif wait_time_minutes < 30:
        return 'warning'
    else:
        return 'critical'


def check_and_alert_sla_breach(submission):
    """
    Check if submission has breached SLA and send alerts if needed.
    
    Args:
        submission: PatientSubmission instance
        
    Side Effects:
        - Creates notification for 25-minute warning (once per submission)
        - Creates notification for 30-minute critical alert (once per submission)
        - Uses submission.metadata to track if alerts already sent
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    # Skip if submission is completed
    if submission.status == "completed":
        return
    
    wait_time = calculate_wait_time(submission)
    
    # Initialize metadata if needed
    if not hasattr(submission, 'metadata'):
        submission.metadata = {}
    
    # Get or initialize SLA alerts tracking
    sla_alerts_sent = submission.metadata.get('sla_alerts_sent', {})
    
    # Check warning threshold (25 minutes)
    if wait_time >= 25 and not sla_alerts_sent.get('warning'):
        from triagesync_backend.apps.notifications.services.notification_service import NotificationService
        NotificationService.create_sla_alert(submission, 'warning')
        sla_alerts_sent['warning'] = True
        submission.metadata['sla_alerts_sent'] = sla_alerts_sent
        submission.save(update_fields=['metadata'])
        logger.info(f"SLA warning alert sent for submission {submission.id} at {wait_time:.1f} minutes")
    
    # Check critical threshold (30 minutes)
    if wait_time >= 30 and not sla_alerts_sent.get('critical'):
        from triagesync_backend.apps.notifications.services.notification_service import NotificationService
        NotificationService.create_sla_alert(submission, 'critical')
        sla_alerts_sent['critical'] = True
        submission.metadata['sla_alerts_sent'] = sla_alerts_sent
        submission.save(update_fields=['metadata'])
        logger.info(f"SLA critical alert sent for submission {submission.id} at {wait_time:.1f} minutes")


def get_wait_time_analytics():
    """
    Calculate comprehensive wait time analytics.
    
    Returns:
        {
            'avg_wait_active': float,  # Average for waiting/in_progress
            'avg_wait_completed_24h': float,  # Average for completed in last 24h
            'max_wait_active': float,  # Maximum among active cases
            'sla_warning_count': int,  # Count with wait_time >= 25min
            'sla_breach_count': int,  # Count with wait_time >= 30min
            'wait_time_trends': list[float],  # 12 hourly averages
        }
        
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 8.1, 8.2, 8.3, 8.4
    """
    now = timezone.now()
    
    # Get active submissions (waiting or in_progress)
    active_submissions = PatientSubmission.objects.filter(status__in=["waiting", "in_progress"])

    # Annotate wait duration = now - created_at and compute DB-side aggregates
    wait_expr = ExpressionWrapper(Now() - F("created_at"), output_field=DurationField())
    annotated_active = active_submissions.annotate(wait=wait_expr)

    avg_wait_active = 0.0
    max_wait_active = 0.0
    sla_warning_count = 0
    sla_breach_count = 0

    if annotated_active.exists():
        agg = annotated_active.aggregate(avg_wait=Avg("wait"), max_wait=Max("wait"))
        avg_wait_duration = agg.get("avg_wait")
        max_wait_duration = agg.get("max_wait")
        if avg_wait_duration:
            avg_wait_active = round(avg_wait_duration.total_seconds() / 60.0, 1)
        if max_wait_duration:
            max_wait_active = round(max_wait_duration.total_seconds() / 60.0, 1)

        sla_warning_count = annotated_active.filter(wait__gte=timezone.timedelta(minutes=25), wait__lt=timezone.timedelta(minutes=30)).count()
        sla_breach_count = annotated_active.filter(wait__gte=timezone.timedelta(minutes=30)).count()
    
    # Get completed submissions in last 24 hours. Use Coalesce(processed_at, Now())
    twenty_four_hours_ago = now - timedelta(hours=24)
    completed_24h = PatientSubmission.objects.filter(status="completed", created_at__gte=twenty_four_hours_ago)

    if completed_24h.exists():
        completed_wait_expr = ExpressionWrapper(Coalesce(F('processed_at'), Now()) - F('created_at'), output_field=DurationField())
        agg_completed = completed_24h.annotate(wait=completed_wait_expr).aggregate(avg_wait=Avg('wait'))
        avg_wait_completed_duration = agg_completed.get('avg_wait')
        avg_wait_completed_24h = round(avg_wait_completed_duration.total_seconds() / 60.0, 1) if avg_wait_completed_duration else 0.0
    else:
        avg_wait_completed_24h = 0.0

    # Calculate hourly wait time trends for last 12 hours using DB-side aggregation
    wait_time_trends = []
    for hour_offset in range(11, -1, -1):  # 11 hours ago to current hour
        hour_start = now - timedelta(hours=hour_offset + 1)
        hour_end = now - timedelta(hours=hour_offset)

        hour_qs = PatientSubmission.objects.filter(created_at__gte=hour_start, created_at__lt=hour_end)
        if hour_qs.exists():
            hour_agg = hour_qs.annotate(wait=ExpressionWrapper(Now() - F('created_at'), output_field=DurationField())).aggregate(avg_wait=Avg('wait'))
            avg_wait_hour_duration = hour_agg.get('avg_wait')
            avg_wait_hour = round(avg_wait_hour_duration.total_seconds() / 60.0, 1) if avg_wait_hour_duration else 0.0
        else:
            avg_wait_hour = 0.0

        wait_time_trends.append(avg_wait_hour)
    
    return {
        'avg_wait_active': avg_wait_active,
        'avg_wait_completed_24h': avg_wait_completed_24h,
        'max_wait_active': max_wait_active,
        'sla_warning_count': sla_warning_count,
        'sla_breach_count': sla_breach_count,
        'wait_time_trends': wait_time_trends,
    }


def get_category_wait_time_analytics():
    """
    Calculate wait time performance by category.
    
    Returns:
        [
            {
                'category': str,
                'avg_wait_time': float,
                'sla_breach_count': int,
                'case_count': int
            },
            ...
        ]
        Ordered by avg_wait_time descending
        
    Requirements: 13.1, 13.2, 13.3, 13.4
    """
    # Get all submissions grouped by category
    all_submissions = PatientSubmission.objects.all()
    
    # Group by category
    category_data = {}
    
    for submission in all_submissions:
        category = submission.category or 'General'
        
        if category not in category_data:
            category_data[category] = {
                'wait_times': [],
                'sla_breaches': 0,
                'case_count': 0
            }
        
        wait_time = calculate_wait_time(submission)
        category_data[category]['wait_times'].append(wait_time)
        category_data[category]['case_count'] += 1
        
        if wait_time >= 30:
            category_data[category]['sla_breaches'] += 1
    
    # Calculate averages and format results
    results = []
    for category, data in category_data.items():
        if data['case_count'] > 0:
            avg_wait_time = round(sum(data['wait_times']) / data['case_count'], 1)
            results.append({
                'category': category,
                'avg_wait_time': avg_wait_time,
                'sla_breach_count': data['sla_breaches'],
                'case_count': data['case_count']
            })
    
    # Sort by average wait time descending
    results.sort(key=lambda x: x['avg_wait_time'], reverse=True)
    
    return results
