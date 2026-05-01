from .models import AuditLog

def log_action(actor, action_type, target_description, justification=None, metadata=None):
    """
    Utility to record administrative actions in the AuditLog.
    """
    AuditLog.objects.create(
        actor=actor,
        action_type=action_type,
        target_description=target_description,
        justification=justification,
        metadata=metadata or {}
    )
