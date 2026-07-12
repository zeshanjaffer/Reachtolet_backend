import logging

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from .auth import user_from_jwt
from .models import ChatMessage
from .presence import (
    broadcast_user_presence,
    contact_user_ids,
    is_online,
    online_user_ids_for_contacts,
    personal_channel,
    set_offline,
    set_online,
)
from .services import (
    ChatError,
    create_message,
    create_room_for_billboard,
    get_room_for_user,
    get_unread_summary,
    mark_message_delivered,
    mark_messages_seen,
    notify_recipient_of_chat_message,
    paginate_messages,
    paginate_rooms,
    serialize_message,
    serialize_room,
)

logger = logging.getLogger(__name__)

# Set by core.asgi after Django loads
sio = None

User = get_user_model()

ROOM_PREFIX = 'chat_room_'


def room_channel(room_id):
    return f'{ROOM_PREFIX}{room_id}'


def register_socket_handlers(socket_server):
    """Attach all event handlers to the AsyncServer instance."""

    @socket_server.event
    async def connect(sid, environ, auth):
        token = None
        if isinstance(auth, dict):
            token = auth.get('token') or auth.get('access')
        if not token:
            qs = environ.get('QUERY_STRING', '')
            for part in qs.split('&'):
                if part.startswith('token='):
                    token = part.split('=', 1)[1]
                    break

        user = await sync_to_async(user_from_jwt)(token)
        if not user:
            return False

        user_name = user.full_name or user.email
        await socket_server.save_session(sid, {'user_id': user.id})
        await socket_server.enter_room(sid, personal_channel(user.id))
        set_online(user.id, sid, user_name)

        online_ids = await sync_to_async(online_user_ids_for_contacts)(user)
        await socket_server.emit(
            'connected',
            {'user_id': user.id, 'online_user_ids': online_ids},
            to=sid,
        )

        contact_ids = await sync_to_async(contact_user_ids)(user)
        await broadcast_user_presence(
            socket_server,
            user.id,
            is_online_flag=True,
            user_name=user_name,
            contact_ids=contact_ids,
        )
        logger.info('Socket connected user=%s sid=%s', user.id, sid)

    @socket_server.event
    async def disconnect(sid):
        try:
            session = await socket_server.get_session(sid)
        except Exception:
            session = None
        user_id = session.get('user_id') if session else None
        if not user_id:
            logger.info('Socket disconnected sid=%s', sid)
            return

        user = await sync_to_async(
            User.objects.filter(pk=user_id, is_active=True).first
        )()
        fully_offline = set_offline(user_id, sid)
        if fully_offline and user:
            contact_ids = await sync_to_async(contact_user_ids)(user)
            await broadcast_user_presence(
                socket_server,
                user_id,
                is_online_flag=False,
                user_name=user.full_name or user.email,
                contact_ids=contact_ids,
            )
        logger.info('Socket disconnected user=%s sid=%s offline=%s', user_id, sid, fully_offline)

    @socket_server.event
    async def chat_sync(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')

        page, page_size = _page_args(data, default_size=20)
        try:
            unread = await sync_to_async(get_unread_summary)(user)
            inbox = await sync_to_async(paginate_rooms)(user, page=page, page_size=page_size)
            online_ids = await sync_to_async(online_user_ids_for_contacts)(user)
        except Exception as exc:
            logger.exception('chat_sync failed: %s', exc)
            return _err(500, 'Failed to sync chat')

        return {
            'status_code': 200,
            'unread': unread,
            'inbox': inbox,
            'online_user_ids': online_ids,
        }

    @socket_server.event
    async def get_unread(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        summary = await sync_to_async(get_unread_summary)(user)
        return {'status_code': 200, **summary}

    @socket_server.event
    async def get_inbox(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        page, page_size = _page_args(data, default_size=20)
        inbox = await sync_to_async(paginate_rooms)(user, page=page, page_size=page_size)
        return {'status_code': 200, **inbox}

    @socket_server.event
    async def get_room(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        room_id = _extract_room_id(data)
        if not room_id:
            return _err(400, 'room_id is required')
        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
            payload = await sync_to_async(serialize_room)(room, user)
        except ChatError as exc:
            return _err(exc.status_code, exc.message)
        return {'status_code': 200, 'room': payload}

    @socket_server.event
    async def get_or_create_room(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        billboard_id = (data or {}).get('billboard_id')
        if not billboard_id:
            return _err(400, 'billboard_id is required')
        try:
            room, created = await sync_to_async(create_room_for_billboard)(
                billboard_id, user
            )
            payload = await sync_to_async(serialize_room)(room, user)
        except ChatError as exc:
            return _err(exc.status_code, exc.message)
        return {
            'status_code': 201 if created else 200,
            'room': payload,
        }

    @socket_server.event
    async def get_messages(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        room_id = _extract_room_id(data)
        if not room_id:
            return _err(400, 'room_id is required')
        page, page_size = _page_args(data, default_size=30)
        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
            payload = await sync_to_async(paginate_messages)(
                room, page=page, page_size=page_size
            )
        except ChatError as exc:
            return _err(exc.status_code, exc.message)
        return {'status_code': 200, **payload}

    @socket_server.event
    async def get_presence(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')
        online_ids = await sync_to_async(online_user_ids_for_contacts)(user)
        return {'status_code': 200, 'online_user_ids': online_ids}

    @socket_server.event
    async def join_room(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            await _emit_error(socket_server, sid, 'Unauthorized', 401)
            return

        room_id = _extract_room_id(data)
        if not room_id:
            await _emit_error(socket_server, sid, 'room_id is required', 400)
            return

        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
        except ChatError as exc:
            await _emit_error(socket_server, sid, exc.message, exc.status_code)
            return

        other = room.other_user(user)
        other_online = is_online(other.id) if other else False

        channel = room_channel(room.id)
        await socket_server.enter_room(sid, channel)
        await socket_server.emit(
            'room_joined',
            {
                'room_id': room.id,
                'other_user_online': other_online,
            },
            to=sid,
        )

    @socket_server.event
    async def leave_room(sid, data):
        room_id = _extract_room_id(data)
        if room_id:
            await socket_server.leave_room(sid, room_channel(room_id))
            await socket_server.emit('room_left', {'room_id': room_id}, to=sid)

    @socket_server.event
    async def typing_start(sid, data):
        await _emit_typing(socket_server, sid, data, is_typing=True)

    @socket_server.event
    async def typing_stop(sid, data):
        await _emit_typing(socket_server, sid, data, is_typing=False)

    @socket_server.event
    async def send_message(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return _err(401, 'Unauthorized')

        room_id = _extract_room_id(data)
        body = (data or {}).get('body', '')
        if not room_id:
            return _err(400, 'room_id is required')

        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
            message, _ = await sync_to_async(create_message)(
                room, user, body=body, files=[]
            )
            payload = await sync_to_async(serialize_message)(message)
            await _fanout_new_message(socket_server, room, user, payload)
            await sync_to_async(notify_recipient_of_chat_message)(room, user, message)
        except ChatError as exc:
            return _err(exc.status_code, exc.message)

        ack = {'status_code': 201, 'message': payload}
        await socket_server.emit('message_sent', ack, to=sid)
        return ack

    @socket_server.event
    async def message_delivered(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return

        room_id = _extract_room_id(data)
        message_id = (data or {}).get('message_id')
        if not room_id or not message_id:
            return

        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)

            def _load_and_mark():
                message = ChatMessage.objects.select_related('sender').get(
                    pk=message_id, room=room
                )
                return mark_message_delivered(message, user)

            message = await sync_to_async(_load_and_mark)()
        except (ChatError, ChatMessage.DoesNotExist):
            return

        await socket_server.emit(
            'message_delivered',
            {
                'room_id': room.id,
                'message_id': message.id,
                'user_id': user.id,
                'status': message.status,
            },
            room=room_channel(room.id),
            skip_sid=sid,
        )

    @socket_server.event
    async def messages_seen(sid, data):
        user = await _session_user(socket_server, sid)
        if not user:
            return

        room_id = _extract_room_id(data)
        message_id = (data or {}).get('message_id')
        if not room_id or not message_id:
            return

        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
            last_message = await sync_to_async(mark_messages_seen)(
                room, user, message_id
            )
            unread = await sync_to_async(get_unread_summary)(user)
        except ChatError:
            return

        await socket_server.emit(
            'unread_updated',
            {'status_code': 200, **unread},
            room=personal_channel(user.id),
        )
        await socket_server.emit(
            'messages_seen',
            {
                'room_id': room.id,
                'message_id': last_message.id,
                'user_id': user.id,
                'status': ChatMessage.STATUS_SEEN,
            },
            room=room_channel(room.id),
            skip_sid=sid,
        )


async def emit_new_message(room_id, payload, recipient=None, room=None, sender=None):
    """Used by REST attachment POST to fan out real-time updates."""
    if sio is None:
        return
    await sio.emit('new_message', payload, room=room_channel(room_id))
    if recipient is not None and room is not None:
        await _notify_recipient_inbox(sio, room, recipient, payload)


async def _fanout_new_message(socket_server, room, sender, payload):
    await socket_server.emit('new_message', payload, room=room_channel(room.id))
    other = room.other_user(sender)
    if other:
        await _notify_recipient_inbox(socket_server, room, other, payload)


async def _notify_recipient_inbox(socket_server, room, recipient, message_payload):
    room_payload = await sync_to_async(serialize_room)(room, recipient)
    unread = await sync_to_async(get_unread_summary)(recipient)
    await socket_server.emit(
        'inbox_updated',
        {
            'room_id': room.id,
            'room': room_payload,
            'last_message': message_payload,
            'updated_at': room_payload.get('updated_at'),
            'unread_count': room_payload.get('unread_count', 0),
        },
        room=personal_channel(recipient.id),
    )
    await socket_server.emit(
        'unread_updated',
        {'status_code': 200, **unread},
        room=personal_channel(recipient.id),
    )


async def _session_user(socket_server, sid):
    session = await socket_server.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return None
    return await sync_to_async(User.objects.filter(pk=user_id, is_active=True).first)()


async def _emit_typing(socket_server, sid, data, is_typing):
    user = await _session_user(socket_server, sid)
    if not user:
        return

    room_id = _extract_room_id(data)
    if not room_id:
        return

    try:
        room = await sync_to_async(get_room_for_user)(room_id, user)
    except ChatError:
        return

    await socket_server.emit(
        'user_typing',
        {
            'room_id': room.id,
            'user_id': user.id,
            'user_name': user.full_name or user.email,
            'is_typing': is_typing,
        },
        room=room_channel(room.id),
        skip_sid=sid,
    )


async def _emit_error(socket_server, sid, message, status_code=400):
    await socket_server.emit(
        'error',
        {'message': message, 'status_code': status_code},
        to=sid,
    )


def _err(status_code, message):
    return {'status_code': status_code, 'message': message}


def _extract_room_id(data):
    if isinstance(data, dict):
        return data.get('room_id')
    return None


def _page_args(data, default_size=20):
    data = data or {}
    try:
        page = int(data.get('page') or 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(data.get('page_size') or default_size)
    except (TypeError, ValueError):
        page_size = default_size
    return max(1, page), max(1, min(page_size, 100))
