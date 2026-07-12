"""In-memory online presence for Socket.IO connections (per server process)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
# user_id -> {'sids': set[str], 'user_name': str}
_presence: dict[int, dict] = {}

USER_PREFIX = 'user_'


def personal_channel(user_id: int) -> str:
    return f'{USER_PREFIX}{user_id}'


def set_online(user_id, sid, user_name=''):
    with _lock:
        entry = _presence.setdefault(int(user_id), {'sids': set(), 'user_name': ''})
        entry['sids'].add(sid)
        if user_name:
            entry['user_name'] = user_name


def set_offline(user_id, sid) -> bool:
    """Remove sid for user. Returns True if the user has no remaining sockets (fully offline)."""
    uid = int(user_id)
    with _lock:
        entry = _presence.get(uid)
        if not entry:
            return True
        entry['sids'].discard(sid)
        if not entry['sids']:
            _presence.pop(uid, None)
            return True
        return False


def is_online(user_id) -> bool:
    with _lock:
        entry = _presence.get(int(user_id))
        return bool(entry and entry['sids'])


def presence_user_name(user_id) -> str:
    with _lock:
        entry = _presence.get(int(user_id))
        return (entry or {}).get('user_name', '') or ''


def contact_user_ids(user) -> set[int]:
    """User IDs who share at least one ChatRoom with this user."""
    from .services import list_rooms_for_user

    rooms = list_rooms_for_user(user).only('advertiser_id', 'media_owner_id')
    ids: set[int] = set()
    for room in rooms:
        if room.advertiser_id == user.id:
            ids.add(room.media_owner_id)
        elif room.media_owner_id == user.id:
            ids.add(room.advertiser_id)
    return ids


def online_user_ids_for_contacts(user) -> list[int]:
    """Among users who share a ChatRoom with this user, who is currently online."""
    contacts = contact_user_ids(user)
    with _lock:
        return sorted(
            uid for uid in contacts if uid in _presence and _presence[uid]['sids']
        )


async def broadcast_user_presence(sio, user_id, *, is_online_flag: bool, user_name='', contact_ids=None):
    """Emit `user_presence` to each contact's personal room `user_{id}`."""
    if sio is None or not contact_ids:
        return
    payload = {
        'user_id': int(user_id),
        'is_online': bool(is_online_flag),
        'user_name': user_name or '',
    }
    for contact_id in contact_ids:
        await sio.emit('user_presence', payload, room=personal_channel(contact_id))
