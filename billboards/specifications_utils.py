"""Parse and validate billboard specifications JSON from API requests."""

from __future__ import annotations

import json

MAX_SPECIFICATIONS_BYTES = 20_480  # 20 KB


def normalize_specifications(value):
    """
    Accept dict or JSON string; return a dict suitable for JSONField storage.
    Frontend may send any keys — backend only enforces object shape and size.
    """
    if value is None or value == '':
        return {}

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError('specifications must be valid JSON.') from exc

    if not isinstance(value, dict):
        raise ValueError('specifications must be a JSON object.')

    encoded = json.dumps(value, separators=(',', ':'))
    if len(encoded.encode('utf-8')) > MAX_SPECIFICATIONS_BYTES:
        raise ValueError(
            f'specifications exceeds maximum size of {MAX_SPECIFICATIONS_BYTES} bytes.'
        )

    return value


def parse_specifications_from_payload(payload):
    """Extract and normalize specifications from request data dict/QueryDict."""
    if 'specifications' not in payload:
        return payload

    data = payload.copy() if hasattr(payload, 'copy') else dict(payload)
    raw = data.get('specifications')
    if raw is None:
        return data

    data['specifications'] = normalize_specifications(raw)
    return data
