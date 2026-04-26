def build_user_profile_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
