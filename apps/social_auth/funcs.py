from typing import Dict

from django.contrib.auth import get_user_model

from apps.core.models import NormalProfile

User = get_user_model()


def register_social_user(full_name: str, email: str, password: str) -> Dict[str, str]:
    """
    Register a social user.

    Args:
        full_name: The full name of the user.
        email: The email address of the user.
        password: The password of the user.

    Returns:
        A dictionary containing the user's email, full name, phone number, and tokens.
        :param password:
        :param email:
        :param full_name:
    """
    user_data = {
        "full_name": full_name,
        "email": email,
        "password": password
    }
    user = User.objects.create_user(**user_data)
    user.email_verified = True
    user.google_provider = True
    NormalProfile.objects.create(user=user)
    user.save()

    return user
