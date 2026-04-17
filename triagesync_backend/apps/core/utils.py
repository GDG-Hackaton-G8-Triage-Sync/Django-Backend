from datetime import datetime
from django.utils import timezone


def get_current_timestamp():
    """Get current UTC timestamp"""
    return timezone.now()


def format_datetime(dt):
    """Format datetime to ISO 8601 string"""
    if dt:
        return dt.isoformat()
    return None


def validate_priority(priority):
    """Validate priority value (1-5)"""
    try:
        priority = int(priority)
        return 1 <= priority <= 5
    except (ValueError, TypeError):
        return False


def validate_urgency_score(score):
    """Validate urgency score (0-100)"""
    try:
        score = int(score)
        return 0 <= score <= 100
    except (ValueError, TypeError):
        return False


def sanitize_input(text, max_length=None):
    """Sanitize user input"""
    if not text:
        return ""

    text = text.strip()

    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text
