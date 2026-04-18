from .models import TriageSession


def get_staff_queue():
    return TriageSession.objects.filter(
        status="in_queue"
    ).order_by("-urgency_score")


def get_current_session():
    return TriageSession.objects.order_by(
        "-created_at"
    ).first()


def get_patient_detail(session_id):
    return TriageSession.objects.get(
        session_id=session_id
    )


def override_priority(session_id, new_priority):
    session = TriageSession.objects.get(
        session_id=session_id
    )

    session.priority_level = new_priority
    session.save()

    reorder_queue()

    return session


def reorder_queue():
    sessions = TriageSession.objects.filter(
        status="in_queue"
    ).order_by("-urgency_score")

    for index, session in enumerate(sessions, start=1):
        session.queue_position = index
        session.save()


def create_triage_session(symptoms):
    return TriageSession.objects.create(
        symptoms=symptoms,
        status="processing"
    )
def update_status(session_id, status):
    session = TriageSession.objects.get(
        session_id=session_id
    )

    session.status = status
    session.save()

    return session
