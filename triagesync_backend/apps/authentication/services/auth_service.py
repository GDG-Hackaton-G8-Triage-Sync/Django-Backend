from django.contrib.auth import get_user_model

User = get_user_model()


def user_exists(email: str) -> bool:
    return User.objects.filter(email=email).exists()
