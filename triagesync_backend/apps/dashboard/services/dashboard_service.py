def summarize_dashboard_row(submission):
    return {
        "id": submission.id,
        "patient": submission.patient_id,
        "created_at": submission.created_at,
    }
