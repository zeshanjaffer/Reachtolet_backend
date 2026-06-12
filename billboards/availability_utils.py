from datetime import datetime
import re

DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def parse_date_param(value):
    if not value:
        return None
    if not DATE_PATTERN.match(value):
        raise ValueError('Invalid date format. Use YYYY-MM-DD.')
    datetime.strptime(value, '%Y-%m-%d')
    return value


def normalize_booked_dates(dates):
    if dates is None:
        return []

    if not isinstance(dates, list):
        raise ValueError('booked_dates must be an array of YYYY-MM-DD strings.')

    normalized = []
    seen = set()
    for raw in dates:
        if raw is None:
            continue
        date_str = str(raw).strip()
        if not DATE_PATTERN.match(date_str):
            raise ValueError('Invalid date format. Use YYYY-MM-DD.')
        datetime.strptime(date_str, '%Y-%m-%d')
        if date_str not in seen:
            seen.add(date_str)
            normalized.append(date_str)

    normalized.sort()
    return normalized


def filter_booked_dates(booked_dates, from_date=None, to_date=None):
    dates = normalize_booked_dates(booked_dates)
    if from_date:
        dates = [d for d in dates if d >= from_date]
    if to_date:
        dates = [d for d in dates if d <= to_date]
    return dates


def build_availability_payload(billboard, from_date=None, to_date=None):
    booked_dates = filter_booked_dates(
        billboard.unavailable_dates or [],
        from_date=from_date,
        to_date=to_date,
    )
    payload = {
        'billboard_id': billboard.id,
        'booked_dates': booked_dates,
        'total_booked': len(booked_dates),
    }
    if from_date:
        payload['from'] = from_date
    if to_date:
        payload['to'] = to_date
    return payload


def get_availability_status(billboard):
    """Return (status, label) for preview/detail UI badges."""
    if not billboard.is_active:
        return 'inactive', 'Inactive'

    today = datetime.now().date().isoformat()
    booked_dates = normalize_booked_dates(billboard.unavailable_dates or [])
    if today in booked_dates:
        return 'booked', 'Booked'

    return 'available', 'Available'
