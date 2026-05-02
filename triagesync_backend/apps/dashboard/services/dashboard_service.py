import logging
from triagesync_backend.apps.patients.models import PatientSubmission
from django.db.models import Avg, Count
from django.utils import timezone
from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_status_changed
from triagesync_backend.apps.core.validators import validate_status_transition

logger = logging.getLogger("dashboard.service")


def get_patient_queue(priority=None, status=None, category=None):
    """
    Fetch patients with optional filtering and intelligent ordering.
    
    Queue Ordering Rules (Triage-Based Priority):
    1. Priority 1 (Critical/Life-threatening) - ALWAYS FIRST
    2. Priority 2 (Emergent/Severe) - SECOND
    3. Priority 3 (Urgent) - THIRD
    4. Priority 4 (Semi-urgent) - FOURTH
    5. Priority 5 (Non-urgent) - LAST
    
    Within each priority level:
    - Sort by urgency_score DESC (higher urgency first)
    - Then by created_at ASC (FIFO - first come, first served)
    
    This ensures:
    - Critical cases (chest pain, stroke, severe bleeding) jump to top
    - Special cases (pregnancy, elderly, immunocompromised) get priority
    - Life-threatening issues are handled immediately
    - Fair ordering within same priority level
    
    Optimized with select_related to prevent N+1 queries
    
    Args:
        priority: Optional priority filter (1-5)
        status: Optional status filter (waiting, in_progress, completed)
        category: Optional category filter (Cardiac, Respiratory, Trauma, Neurological, General)
    
    Returns:
        QuerySet of PatientSubmission ordered by priority, urgency_score, created_at
    """
    queryset = PatientSubmission.objects.select_related('patient__user').all()

    # Apply filters if provided
    if priority:
        queryset = queryset.filter(priority=priority)

    if status:
        queryset = queryset.filter(status=status)

    if category:
        queryset = queryset.filter(category=category)

    # Multi-level sorting:
    # 1. Priority ASC (1 comes before 5)
    # 2. Urgency score DESC (higher urgency first within same priority)
    # 3. Created time ASC (FIFO within same priority and urgency)
    return queryset.order_by("priority", "-urgency_score", "created_at")


def update_patient_status(patient_id, new_status):
    """
    Update workflow status of a patient with validation and broadcast
    """
    logger.info(f"Attempting status update for patient {patient_id} to {new_status}")
    
    try:
        patient = PatientSubmission.objects.get(id=patient_id)
        
        # Validate transition using centralized validator
        try:
            validate_status_transition(patient.status, new_status)
        except ValueError as e:
            logger.warning(f"Invalid status transition for patient {patient_id}: {patient.status} -> {new_status}")
            raise e
        
        # Update status
        old_status = patient.status
        patient.status = new_status
        patient.save()
        
        logger.info(f"Status updated for patient {patient_id}: {old_status} -> {new_status}")
        
        # Broadcast WebSocket event (Member 8)
        broadcast_status_changed(patient_id, new_status)
        logger.info(f"Broadcast event sent for patient {patient_id} status change")
        
        return patient
    except PatientSubmission.DoesNotExist:
        logger.error(f"Patient {patient_id} not found for status update")
        return None
    except ValueError as e:
        # Re-raise validation errors for the view to handle
        raise e


def get_admin_overview():
    """
    Aggregated system stats for Admin Dashboard.
    Aligned with frontend expectations (Enterprise Admin Portal).
    
    Requirements: 6.4, 6.5
    """
    from .wait_time_service import get_wait_time_analytics
    
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate average wait time (created_at to now for waiting/in_progress)
    active_submissions = PatientSubmission.objects.filter(status__in=["waiting", "in_progress"])
    avg_wait = 0
    if active_submissions.exists():
        total_wait_mins = sum((now - s.created_at).total_seconds() / 60 for s in active_submissions)
        avg_wait = total_wait_mins / active_submissions.count()

    # SLA Breach count: Patients waiting > 30 minutes
    sla_threshold = now - timezone.timedelta(minutes=30)
    sla_breaches = PatientSubmission.objects.filter(
        status__in=["waiting", "in_progress"],
        created_at__lt=sla_threshold
    ).count()

    # Get wait time analytics from wait_time_service
    wait_time_analytics = get_wait_time_analytics()

    return {
        "total_patients": PatientSubmission.objects.count(),
        "waiting_patients": PatientSubmission.objects.filter(status="waiting").count(),
        "in_progress_patients": PatientSubmission.objects.filter(status="in_progress").count(),
        "completed_today": PatientSubmission.objects.filter(status="completed", processed_at__gte=today_start).count(),
        "critical_cases": PatientSubmission.objects.filter(priority=1).count(),
        "sla_breaches": sla_breaches,
        "average_wait_time_minutes": round(avg_wait, 1),
        "sla_warning_count": wait_time_analytics['sla_warning_count'],  # NEW: Cases at 25-30 minutes
        "max_wait_time_minutes": wait_time_analytics['max_wait_active'],  # NEW: Longest current wait
    }


def get_admin_analytics():
    """
    Detailed analytics for Admin Dashboard (Command Center).
    Provides time-series data for Wait Time Trends and SLA Breach Velocity.
    
    Requirements: 8.1, 8.2, 8.3, 13.1, 13.2, 13.3
    """
    from .wait_time_service import get_wait_time_analytics, get_category_wait_time_analytics
    
    now = timezone.now()
    
    # 1. Get wait time analytics from wait_time_service (Requirements 8.1, 8.2, 8.3)
    wait_time_analytics = get_wait_time_analytics()
    wait_time_trends = wait_time_analytics['wait_time_trends']  # 12 hourly values
    
    # 2. Calculate SLA Breach Velocity (Last 12 Hours)
    sla_breach_velocity = []
    
    for i in range(11, -1, -1):
        hour_start = now - timezone.timedelta(hours=i)
        hour_end = hour_start + timezone.timedelta(hours=1)
        
        # Submissions handled in this hour window
        hour_submissions = PatientSubmission.objects.filter(
            created_at__gte=hour_start,
            created_at__lt=hour_end
        )
        
        # Count breaches (exceeding 30m target)
        breaches = 0
        for s in hour_submissions:
            if s.processed_at:
                if (s.processed_at - s.created_at).total_seconds() / 60 > 30:
                    breaches += 1
            elif (now - s.created_at).total_seconds() / 60 > 30:
                breaches += 1
        sla_breach_velocity.append(breaches)

    # 3. Common Conditions Mapping
    conditions_query = (
        PatientSubmission.objects.values("category")
        .annotate(count=Count("category"))
        .order_by("-count")[:5]
    )
    common_conditions = {
        item["category"] or "General": item["count"] 
        for item in conditions_query
    }

    # 4. Category Distribution (Requirements 3.1, 3.2, 3.3, 3.4)
    # Calculate count of PatientSubmissions for each category
    # Return ordered by case count descending
    # Exclude categories with zero cases
    category_distribution_query = (
        PatientSubmission.objects.values("category")
        .annotate(count=Count("id"))
        .filter(count__gt=0)  # Exclude categories with zero cases
        .order_by("-count")  # Order by case count descending
    )
    category_distribution = {
        item["category"] or "General": item["count"]
        for item in category_distribution_query
    }

    # 5. Get category wait time analytics (Requirements 13.1, 13.2, 13.3)
    category_wait_times = get_category_wait_time_analytics()

    # 6. Peak usage time
    from django.db.models.functions import ExtractHour
    peak_hour_query = (
        PatientSubmission.objects.annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    peak_usage_time = f"{peak_hour_query['hour']:02d}:00" if peak_hour_query else "N/A"

    avg_urgency = PatientSubmission.objects.aggregate(Avg("urgency_score"))["urgency_score__avg"] or 0

    return {
        "avg_urgency_score": round(avg_urgency, 1),
        "peak_usage_time": peak_usage_time,
        "common_conditions": common_conditions,
        "category_distribution": category_distribution,  # Category distribution
        "wait_time_trends": wait_time_trends,  # NEW: 12 hourly wait time values from wait_time_service
        "sla_breach_velocity": sla_breach_velocity,
        "category_wait_times": category_wait_times,  # NEW: Performance by category
        "peak_hour": peak_usage_time,
    }

def update_priority(patient, priority):
    """
    Update patient priority with validation and real-time broadcast.
    
    When priority changes, the patient's position in the queue automatically
    changes based on the new priority level. This ensures critical cases
    always move to the top of the queue.
    
    Priority Levels:
    - 1: Critical/Life-threatening (chest pain, stroke, severe bleeding)
    - 2: Emergent/Severe (high fever, moderate trauma)
    - 3: Urgent (persistent symptoms)
    - 4: Semi-urgent (minor issues)
    - 5: Non-urgent (routine care)
    """
    logger.info(f"Updating priority for patient {patient.id} to {priority}")
    
    # Validate priority range
    if not isinstance(priority, int) or priority < 1 or priority > 5:
        logger.error(f"Invalid priority value: {priority}. Must be 1-5.")
        raise ValueError("Priority must be an integer between 1 and 5")
    
    old_priority = patient.priority
    patient.priority = priority
    
    # If priority changed to critical (1), also update urgency_score to ensure top position
    if priority == 1 and patient.urgency_score < 80:
        logger.warning(f"Patient {patient.id} set to priority 1 but urgency_score is {patient.urgency_score}. Adjusting to 85.")
        patient.urgency_score = max(patient.urgency_score, 85)
    
    patient.save()
    logger.info(f"Priority updated for patient {patient.id}: {old_priority} -> {priority}")
    
    # Broadcast priority update event (Member 8) - triggers queue reordering on frontend
    from triagesync_backend.apps.realtime.services.broadcast_service import broadcast_priority_update
    broadcast_priority_update(patient.id, priority, patient.urgency_score)
    logger.info(f"Broadcast priority update event for patient {patient.id}")
    
    return patient


def verify_patient(patient, user):
    if patient.verified_at:
        logger.info(f"Patient {patient.id} already verified, skipping")
        return None

    logger.info(f"Verifying patient {patient.id} by user {user.username}")
    patient.verified_by_user = user
    patient.verified_at = timezone.now()
    patient.save()
    logger.info(f"Patient {patient.id} verified successfully by {user.username}")
    return patient
