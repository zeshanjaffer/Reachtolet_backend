"""Email helpers for password-reset OTP delivery."""

from __future__ import annotations

import base64
import logging
import os
from email.mime.text import MIMEText

import requests

logger = logging.getLogger(__name__)

GMAIL_SEND_SCOPE = 'https://www.googleapis.com/auth/gmail.send'
GMAIL_SEND_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
TOKEN_URL = 'https://oauth2.googleapis.com/token'


def _gmail_env():
    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip()
    client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip()
    refresh_token = os.environ.get('GOOGLE_GMAIL_REFRESH_TOKEN', '').strip()
    if not (client_id and client_secret and refresh_token):
        return None
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
    }


def gmail_configured() -> bool:
    return _gmail_env() is not None


def _refresh_access_token(env: dict) -> str:
    """Refresh Gmail access token via OAuth token endpoint (no google-auth required at import)."""
    try:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=None,
            refresh_token=env['refresh_token'],
            token_uri=TOKEN_URL,
            client_id=env['client_id'],
            client_secret=env['client_secret'],
            scopes=[GMAIL_SEND_SCOPE],
        )
        creds.refresh(GoogleAuthRequest())
        return creds.token
    except ImportError:
        resp = requests.post(
            TOKEN_URL,
            data={
                'client_id': env['client_id'],
                'client_secret': env['client_secret'],
                'refresh_token': env['refresh_token'],
                'grant_type': 'refresh_token',
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f'Token refresh failed: {resp.status_code}')
        return resp.json()['access_token']


def send_otp_email(to_email: str, otp: str) -> None:
    """
    Send password-reset OTP.

    Uses Gmail API when GOOGLE_OAUTH_CLIENT_ID/SECRET and GOOGLE_GMAIL_REFRESH_TOKEN
    are set; otherwise logs the OTP for local/dev and returns successfully.
    Raises RuntimeError if Gmail is configured but sending fails (caller -> 503).
    """
    subject = 'Your Reachtolet password reset code'
    body = (
        f'Your password reset code is: {otp}\n\n'
        'This code expires in 10 minutes. If you did not request a reset, ignore this email.'
    )

    env = _gmail_env()
    if env is None:
        logger.info(
            'Password reset OTP for %s: %s (Gmail not configured; logged for dev)',
            to_email,
            otp,
        )
        return

    try:
        access_token = _refresh_access_token(env)
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        resp = requests.post(
            GMAIL_SEND_URL,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={'raw': raw},
            timeout=30,
        )
        if resp.status_code >= 400:
            logger.error('Gmail send failed: status=%s body=%s', resp.status_code, resp.text)
            raise RuntimeError('Failed to send email via Gmail')
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception('Gmail send error: %s', exc)
        raise RuntimeError('Failed to send email via Gmail') from exc
