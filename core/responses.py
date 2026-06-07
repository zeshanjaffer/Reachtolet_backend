from rest_framework.response import Response


def action_response(message, status_code):
    """Standard minimal response for POST action endpoints."""
    return Response(
        {
            'status_code': status_code,
            'message': message,
        },
        status=status_code,
    )


def auth_response(message, status_code, access, refresh, user=None):
    """Auth response with JWT tokens for login, register, and refresh."""
    payload = {
        'status_code': status_code,
        'message': message,
        'access': access,
        'refresh': refresh,
    }
    if user is not None:
        payload['user'] = user
    return Response(payload, status=status_code)
