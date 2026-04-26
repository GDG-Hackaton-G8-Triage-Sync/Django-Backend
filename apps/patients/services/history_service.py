def build_history_entry(submission):
    return {
        "id": submission.id,
        "symptoms": submission.symptoms,
        "created_at": submission.created_at,
    }
