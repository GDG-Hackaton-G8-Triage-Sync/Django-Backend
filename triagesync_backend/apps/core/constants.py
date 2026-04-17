class UserRole:
    PATIENT = 'patient'
    STAFF = 'staff'
    ADMIN = 'admin'

    CHOICES = [
        (PATIENT, 'Patient'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]


class PatientStatus:
    WAITING = 'waiting'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

    CHOICES = [
        (WAITING, 'Waiting'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]


class TriagePriority:
    CRITICAL = 1      # Life-threatening
    HIGH = 2          # Urgent
    MODERATE = 3      # Moderate
    LOW = 4           # Low urgency
    MINIMAL = 5       # Minimal urgency

    CHOICES = [
        (CRITICAL, 'Critical'),
        (HIGH, 'High'),
        (MODERATE, 'Moderate'),
        (LOW, 'Low'),
        (MINIMAL, 'Minimal'),
    ]


# WebSocket Event Types
class WSEventType:
    PATIENT_CREATED = 'patient_created'
    PATIENT_UPDATE = 'patient_update'
    PRIORITY_UPDATE = 'priority_update'
    STATUS_UPDATE = 'status_update'
    TRIAGE_UPDATE = 'triage_update'
    CRITICAL_ALERT = 'critical_alert'
    SYSTEM_ALERT = 'system_alert'


# AI Service Providers
class AIProvider:
    OPENAI = 'openai'
    GEMINI = 'gemini'


# Triage Status
class TriageStatus:
    PROCESSED = 'processed'
    FALLBACK = 'fallback'
    ERROR = 'error'
