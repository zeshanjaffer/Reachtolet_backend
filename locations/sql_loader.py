"""
Parse MySQL INSERT ... VALUES rows from SQL dump files.
"""
import json
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from typing import Any, Generator, List, Optional

INSERT_PREFIX_RE = re.compile(
    r"INSERT\s+INTO\s+`(?P<table>[^`]+)`\s+VALUES\s*",
    re.IGNORECASE,
)


def _parse_mysql_value(text: str, index: int) -> tuple[Any, int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length:
        raise ValueError('Unexpected end of input while parsing MySQL value')

    char = text[index]
    if char == "'":
        index += 1
        chars: list[str] = []
        while index < length:
            char = text[index]
            if char == '\\' and index + 1 < length:
                chars.append(text[index + 1])
                index += 2
                continue
            if char == "'":
                return ''.join(chars), index + 1
            chars.append(char)
            index += 1
        raise ValueError('Unterminated MySQL string literal')

    if text.startswith('NULL', index):
        return None, index + 4

    start = index
    if char == '-':
        index += 1
    while index < length and (text[index].isdigit() or text[index] in '.eE+-'):
        index += 1
    raw = text[start:index]
    if '.' in raw or 'e' in raw.lower():
        return float(raw), index
    return int(raw), index


def _parse_mysql_row(text: str, index: int) -> tuple[Optional[List[Any]], int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] != '(':
        return None, index

    index += 1
    values: list[Any] = []
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index < length and text[index] == ')':
            return values, index + 1

        value, index = _parse_mysql_value(text, index)
        values.append(value)

        while index < length and text[index].isspace():
            index += 1
        if index < length and text[index] == ',':
            index += 1
            continue
        if index < length and text[index] == ')':
            return values, index + 1

    raise ValueError('Unterminated MySQL row tuple')


def iter_mysql_insert_rows(sql_path: Path, table_name: str) -> Generator[List[Any], None, None]:
    """Yield parsed row value lists for a given table from a MySQL dump file."""
    buffer = ''
    target = table_name.lower()

    with sql_path.open('r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            match = INSERT_PREFIX_RE.search(line)
            if not match or match.group('table').lower() != target:
                continue

            payload = line[match.end():].strip()
            if payload.endswith(';'):
                payload = payload[:-1]
            buffer += payload

            index = 0
            while index < len(buffer):
                while index < len(buffer) and buffer[index] not in '(),':
                    index += 1
                if index >= len(buffer):
                    break

                if buffer[index] == '(':
                    row, index = _parse_mysql_row(buffer, index)
                    if row is not None:
                        yield row
                    continue

                if buffer[index] == ',':
                    index += 1
                    continue

                break

            buffer = buffer[index:]


def _as_bool(value: Any) -> bool:
    if value is None:
        return False
    return bool(int(value))


def _as_str(value: Any, default: str = '') -> str:
    if value is None:
        return default
    return str(value)


def _as_json(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, (list, dict)):
        return value
    return json.loads(value)


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def parse_lat_lng(
    coordinates: Any = None,
    latitude: Any = None,
    longitude: Any = None,
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    lat = _to_decimal(latitude)
    lng = _to_decimal(longitude)
    if lat is not None and lng is not None:
        return lat, lng

    if coordinates:
        parts = [part.strip() for part in str(coordinates).split(',') if part.strip()]
        if len(parts) >= 2:
            parsed_lat = _to_decimal(parts[0])
            parsed_lng = _to_decimal(parts[1])
            if parsed_lat is not None and parsed_lng is not None:
                return parsed_lat, parsed_lng

    return lat, lng


def map_state_row(row: List[Any]) -> dict[str, Any]:
    latitude, longitude = parse_lat_lng(coordinates=row[4])
    return {
        'legacy_id': row[0],
        'name': row[1],
        'abbr': row[2],
        'capital': row[3],
        'coordinates': row[4],
        'latitude': latitude,
        'longitude': longitude,
        'enabled': _as_bool(row[5]),
        'deleted_at': row[6],
        'country_id': row[7],
        'image': _as_str(row[8]),
        'region': _as_str(row[9]),
    }


def map_city_row(row: List[Any]) -> dict[str, Any]:
    latitude_text = _as_str(row[12])
    longitude_text = _as_str(row[13])
    parsed_lat, parsed_lng = parse_lat_lng(
        coordinates=row[3],
        latitude=latitude_text,
        longitude=longitude_text,
    )
    if parsed_lat is not None and not latitude_text:
        latitude_text = str(parsed_lat)
    if parsed_lng is not None and not longitude_text:
        longitude_text = str(parsed_lng)

    return {
        'legacy_id': row[0],
        'state_abbr': row[1],
        'name': row[2],
        'coordinates': row[3],
        'enabled': _as_bool(row[4]),
        'deleted_at': row[5],
        'country_id': row[6],
        'image': _as_str(row[7]),
        'county_name': _as_str(row[8]),
        'state_name': _as_str(row[9]),
        'zip_codes': _as_str(row[10]),
        'place_type': _as_str(row[11]),
        'latitude': latitude_text,
        'longitude': longitude_text,
        'area_code': _as_str(row[14]),
        'population': _as_str(row[15]),
        'households': _as_str(row[16]),
        'median_income': _as_str(row[17]),
        'land_area': _as_str(row[18]),
        'water_area': _as_str(row[19]),
        'time_zone': _as_str(row[20]),
    }


def map_city_boundary_row(row: List[Any]) -> dict[str, Any]:
    return {
        'legacy_id': row[0],
        'city': row[1],
        'state': row[2],
        'boundary': _as_json(row[3]),
        'deleted_at': row[4],
    }


def map_state_boundary_row(row: List[Any]) -> dict[str, Any]:
    return {
        'legacy_id': row[0],
        'state': row[1],
        'boundary': _as_json(row[2]),
        'deleted_at': row[3],
    }


def count_rows(sql_path: Path, table_name: str) -> int:
    return sum(1 for _ in iter_mysql_insert_rows(sql_path, table_name))
