import logging

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from .auth import user_from_jwt
from .models import ChatMessage
from .services import (
    ChatError,
    create_message,
    get_room_for_user,
    mark_message_delivered,
    mark_messages_seen,
    serialize_message,
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

        await socket_server.save_session(sid, {'user_id': user.id})
        await socket_server.emit('connected', {'user_id': user.id}, to=sid)
        logger.info('Socket connected user=%s sid=%s', user.id, sid)

    @socket_server.event
    async def disconnect(sid):
        logger.info('Socket disconnected sid=%s', sid)

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

        channel = room_channel(room.id)
        await socket_server.enter_room(sid, channel)
        await socket_server.emit('room_joined', {'room_id': room.id}, to=sid)

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
        """Optional real-time send (REST POST is preferred when uploading files)."""
        user = await _session_user(socket_server, sid)
        if not user:
            await _emit_error(socket_server, sid, 'Unauthorized', 401)
            return

        room_id = _extract_room_id(data)
        body = (data or {}).get('body', '')
        if not room_id:
            await _emit_error(socket_server, sid, 'room_id is required', 400)
            return

        try:
            room = await sync_to_async(get_room_for_user)(room_id, user)
            message, _ = await sync_to_async(create_message)(room, user, body=body, files=[])
            payload = await sync_to_async(serialize_message)(message)
        except ChatError as exc:
            await _emit_error(socket_server, sid, exc.message, exc.status_code)
            return

        await socket_server.emit('new_message', payload, room=room_channel(room.id))

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
            message = await sync_to_async(ChatMessage.objects.select_related('sender').get)(
                pk=message_id, room=room
            )
            message = await sync_to_async(mark_message_delivered)(message, user)
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
            last_message = await sync_to_async(mark_messages_seen)(room, user, message_id)
        except ChatError:
            return

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


async def emit_new_message(room_id, payload):
    if sio is None:
        return
    await sio.emit('new_message', payload, room=room_channel(room_id))


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


def _extract_room_id(data):
    if isinstance(data, dict):
        return data.get('room_id')
    return None
