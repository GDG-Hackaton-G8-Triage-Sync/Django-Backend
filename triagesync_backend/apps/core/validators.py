"""
Centralized validation utilities for TriageSync Backend

Member 1 (Core Infrastructure) responsibilities:
- Input validation utilities
- Data format validation
- Business rule validation helpers
"""

from django.core.exceptions import ValidationError


def validate_description_length(value):
    """
    Validate description field length (API contract field name)
    
    Args:
        value (str): Description text to validate
        
    Raises:
        ValidationError: If description exceeds 500 characters
    """
    if not isinstance(value, str):
        raise ValidationError("Description must be a string")
    
    if len(value) > 500:
        raise ValidationError("Description cannot exceed 500 characters")
    
    if not value.strip():
        raise ValidationError("Description cannot be empty")


def validate_priority(value):
    """
    Validate priority level (1-5 range)
    
    Args:
        value (int): Priority level to validate
        
    Raises:
        ValidationError: If priority is not in 1-5 range
    """
    if not isinstance(value, int):
        raise ValidationError("Priority must be an integer")
    
    if not (1 <= value <= 5):
        raise ValidationError("Priority must be between 1 and 5")


def validate_urgency_score(value):
    """
    Validate urgency score (0-100 range)
    
    Args:
        value (int): Urgency score to validate
        
    Raises:
        ValidationError: If urgency score is not in 0-100 range
    """
    if not isinstance(value, int):
        raise ValidationError("Urgency score must be an integer")
    
    if not (0 <= value <= 100):
        raise ValidationError("Urgency score must be between 0 and 100")


def validate_status_transition(current_status, new_status):
    """
    Validate status transition per workflow rules
    
    Valid transitions:
    - waiting -> in_progress
    - in_progress -> completed
    - waiting -> completed (skip in_progress)
    - waiting -> canceled
    - in_progress -> canceled
    
    Invalid transitions:
    - completed -> any other status
    - in_progress -> waiting (regression)
    
    Args:
        current_status (str): Current status
        new_status (str): Desired new status
        
    Returns:
        bool: True if transition is valid
        
    Raises:
        ValidationError: If transition is invalid
    """
    valid_statuses = ['waiting', 'in_progress', 'completed', 'canceled']
    
    if current_status not in valid_statuses:
        raise ValidationError(f"Invalid current status: {current_status}")
    
    if new_status not in valid_statuses:
        raise ValidationError(f"Invalid new status: {new_status}")
    
    # Same status is always valid (no-op)
    if current_status == new_status:
        return True
    
    # Define valid transitions
    valid_transitions = {
        'waiting': ['in_progress', 'completed'],
        'in_progress': ['completed'],
        'completed': [],  # No transitions from completed
        'canceled': [],
    }
    
    if new_status not in valid_transitions[current_status]:
        raise ValidationError(
            f"Invalid status transition: {current_status} -> {new_status}"
        )
    
    return True


def validate_role(value):
    """
    Validate user role
    
    Args:
        value (str): Role to validate
        
    Raises:
        ValidationError: If role is not valid
    """
    valid_roles = ['patient', 'nurse', 'doctor', 'admin', 'staff']
    
    if value not in valid_roles:
        raise ValidationError(f"Invalid role: {value}. Must be one of {valid_roles}")


def validate_photo_name(value):
    """
    Validate photo filename
    
    Args:
        value (str): Photo filename to validate
        
    Raises:
        ValidationError: If filename is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Photo name must be a string")
    
    if len(value) > 255:
        raise ValidationError("Photo name cannot exceed 255 characters")
    
    # Basic filename validation (no path traversal)
    if '..' in value or '/' in value or '\\' in value:
        raise ValidationError("Photo name contains invalid characters")


# Validation helper functions for common patterns
def is_valid_description(value):
    """Check if description is valid without raising exception"""
    try:
        validate_description_length(value)
        return True
    except ValidationError:
        return False


def is_valid_priority(value):
    """Check if priority is valid without raising exception"""
    try:
        validate_priority(value)
        return True
    except ValidationError:
        return False


def is_valid_urgency_score(value):
    """Check if urgency score is valid without raising exception"""
    try:
        validate_urgency_score(value)
        return True
    except ValidationError:
        return False


def is_valid_status_transition(current_status, new_status):
    """Check if status transition is valid without raising exception"""
    try:
        validate_status_transition(current_status, new_status)
        return True
    except ValidationError:
        return False