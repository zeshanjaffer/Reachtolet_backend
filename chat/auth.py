"""JWT authentication helpers for Socket.IO connections."""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def user_from_jwt(token: str | None):
    if not token:
        return None
    raw = token.strip()
    if raw.lower().startswith('bearer '):
        raw = raw[7:].strip()
    if not raw:
        return None
    try:
        validated = AccessToken(raw)
        user_id = validated.get('user_id')
        if not user_id:
            return None
        return User.objects.filter(pk=user_id, is_active=True).first()
    except (InvalidToken, TokenError, User.DoesNotExist):
        return None
