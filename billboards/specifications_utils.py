"""Parse and validate billboard specifications JSON from API requests."""

from __future__ import annotations

import json

MAX_SPECIFICATIONS_BYTES = 20_480  # 20 KB


def normalize_specifications(value):
    """
    Accept dict or JSON string; return a dict suitable for JSONField storage.
    Rejects currency key; enforces object shape and size.
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

    if 'currency' in value:
        raise ValueError('_unknown')

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


def _coerce_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _validate_field_value(attr, value):
    """Return error message string or None if valid."""
    field_type = attr.field_type
    rules = attr.validation if isinstance(attr.validation, dict) else {}

    if field_type == 'text':
        # Allow nested JSON (e.g. slots arrays) as well as plain strings
        if isinstance(value, (list, dict)):
            return None
        if not isinstance(value, str):
            return 'Must be a string or JSON value.'
        min_len = rules.get('min_length')
        max_len = rules.get('max_length')
        if min_len is not None and len(value) < int(min_len):
            return f'Must be at least {min_len} characters.'
        if max_len is not None and len(value) > int(max_len):
            return f'Must be at most {max_len} characters.'
        return None

    if field_type == 'boolean':
        if not isinstance(value, bool):
            return 'Must be a boolean.'
        return None

    if field_type == 'integer':
        if isinstance(value, bool) or not isinstance(value, int):
            # reject bool (subclass of int) and non-int floats/strings
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            elif isinstance(value, str) and value.strip().lstrip('-').isdigit():
                value = int(value.strip())
            else:
                return 'Must be an integer.'
        min_v = rules.get('min')
        max_v = rules.get('max')
        if min_v is not None and value < int(min_v):
            return f'Must be at least {min_v}.'
        if max_v is not None and value > int(max_v):
            return f'Must be at most {max_v}.'
        return None

    if field_type == 'number':
        num = _coerce_number(value)
        if num is None:
            return 'Must be a number.'
        min_v = rules.get('min')
        max_v = rules.get('max')
        if min_v is not None and num < float(min_v):
            return f'Must be at least {min_v}.'
        if max_v is not None and num > float(max_v):
            return f'Must be at most {max_v}.'
        return None

    if field_type == 'select':
        options = attr.options if isinstance(attr.options, list) else []
        if value not in options:
            return f'Must be one of: {options}.'
        return None

    if field_type == 'multiselect':
        if not isinstance(value, list):
            return 'Must be a list.'
        options = attr.options if isinstance(attr.options, list) else []
        for item in value:
            if item not in options:
                return f'Invalid option {item!r}. Allowed: {options}.'
        return None

    return None


def validate_specifications_against_attributes(specifications, media_type):
    """
    Validate specs against active OohMediaTypeAttribute rows for media_type.

    Returns a dict of field errors (empty if valid). Caller should raise under
    the `specifications` key.
    """
    if media_type is None:
        return {}

    attributes = list(
        media_type.attributes.filter(is_active=True).order_by('order', 'id')
    )
    if not attributes:
        return {}

    specs = specifications if isinstance(specifications, dict) else {}
    errors = {}
    known_keys = {attr.key for attr in attributes}

    if 'currency' in specs:
        errors['currency'] = 'currency is not allowed in specifications'

    for key in specs:
        if key == 'currency':
            continue
        if key not in known_keys:
            errors[key] = 'Unknown specification key for this media type.'

    for attr in attributes:
        if attr.key not in specs:
            if attr.required:
                errors[attr.key] = 'This field is required.'
            continue
        msg = _validate_field_value(attr, specs[attr.key])
        if msg:
            errors[attr.key] = msg

    return errors
