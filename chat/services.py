"""Chat business logic shared by REST and Socket.IO."""

from __future__ import annotations

import math
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from billboards.models import Billboard

from .models import ChatAttachment, ChatMessage, ChatRoom, ChatRoomParticipant

MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_ATTACHMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/jpg',
    'text/plain',
}


class ChatError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_room_for_user(room_id, user):
    try:
        room = ChatRoom.objects.select_related(
            'billboard', 'advertiser', 'media_owner'
        ).get(pk=room_id)
    except ChatRoom.DoesNotExist as exc:
        raise ChatError('Chat room not found.', 404) from exc

    if not room.is_participant(user):
        raise ChatError('You are not a participant in this chat room.', 403)
    return room


def get_or_create_room(billboard_id, advertiser_user):
    """Advertiser initiates chat from billboard detail (OLX-style)."""
    if advertiser_user.user_type != 'advertiser':
        raise ChatError('Only advertisers can start a chat from a billboard.', 403)

    try:
        billboard = Billboard.objects.select_related('user').get(pk=billboard_id)
    except Billboard.DoesNotExist as exc:
        raise ChatError('Billboard not found.', 404) from exc

    if not billboard.user_id:
        raise ChatError('This billboard has no media owner assigned.', 400)

    if billboard.user_id == advertiser_user.id:
        raise ChatError('You cannot chat with yourself on your own billboard.', 400)

    media_owner = billboard.user

    with transaction.atomic():
        room, created = ChatRoom.objects.get_or_create(
            billboard=billboard,
            advertiser=advertiser_user,
            defaults={'media_owner': media_owner},
        )
        _ensure_participants(room)
    return room, created


def create_room_for_billboard(billboard_id, user):
    """Alias for get_or_create_room — avoids collision with the socket event name."""
    return get_or_create_room(billboard_id, user)


def get_room_by_billboard(billboard_id, user):
    """Return existing room for this user + billboard, or None."""
    try:
        billboard = Billboard.objects.get(pk=billboard_id)
    except Billboard.DoesNotExist as exc:
        raise ChatError('Billboard not found.', 404) from exc

    if user.user_type == 'advertiser':
        return ChatRoom.objects.filter(billboard=billboard, advertiser=user).first()
    if user.user_type == 'media_owner' and billboard.user_id == user.id:
        advertiser_id = None  # media owner may have many rooms per billboard
        return None
    if user.user_type == 'media_owner':
        return ChatRoom.objects.filter(billboard=billboard, media_owner=user).first()
    return None


def list_rooms_for_user(user):
    if user.user_type == 'advertiser':
        return ChatRoom.objects.filter(advertiser=user)
    if user.user_type == 'media_owner':
        return ChatRoom.objects.filter(media_owner=user)
    return ChatRoom.objects.none()


def _clamp_page(page, page_size, default_size):
    try:
        page = int(page or 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(page_size or default_size)
    except (TypeError, ValueError):
        page_size = default_size
    return max(1, page), max(1, min(page_size, 100))


def paginate_rooms(user, page=1, page_size=20):
    """Paginated inbox for socket get_inbox / chat_sync."""
    page, page_size = _clamp_page(page, page_size, 20)
    qs = (
        list_rooms_for_user(user)
        .select_related('billboard', 'advertiser', 'media_owner')
        .order_by('-updated_at')
    )
    total = qs.count()
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    start = (page - 1) * page_size
    rooms = list(qs[start:start + page_size])
    return {
        'count': total,
        'total_pages': total_pages,
        'current_page': page,
        'page_size': page_size,
        'results': [serialize_room(room, user) for room in rooms],
    }


def paginate_messages(room, page=1, page_size=30):
    """
    Paginated messages for socket get_messages.
    Page 1 is the newest page (like REST); results within the page are
    chronological ascending (oldest first) as Flutter expects.
    """
    page, page_size = _clamp_page(page, page_size, 30)
    qs = (
        ChatMessage.objects.filter(room=room)
        .select_related('sender')
        .prefetch_related('attachments')
        .order_by('-created_at')
    )
    total = qs.count()
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    start = (page - 1) * page_size
    page_items = list(qs[start:start + page_size])
    page_items.reverse()
    return {
        'count': total,
        'total_pages': total_pages,
        'current_page': page,
        'page_size': page_size,
        'results': [serialize_message(message) for message in page_items],
    }


def _ensure_participants(room):
    for participant_user in (room.advertiser, room.media_owner):
        ChatRoomParticipant.objects.get_or_create(room=room, user=participant_user)


def _absolute_file_url(file_url, request=None):
    if not file_url:
        return file_url
    if file_url.startswith('http://') or file_url.startswith('https://'):
        return file_url
    if request is not None:
        return request.build_absolute_uri(file_url)
    base = getattr(settings, 'PUBLIC_BASE_URL', '') or ''
    base = base.rstrip('/')
    if not base:
        return file_url
    if not file_url.startswith('/'):
        file_url = f'/{file_url}'
    return f'{base}{file_url}'


def _save_uploaded_file(file_obj, request=None):
    content_type = getattr(file_obj, 'content_type', '') or 'application/octet-stream'
    if content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise ChatError(f'File type not allowed: {content_type}', 400)

    size = file_obj.size
    if size > MAX_ATTACHMENT_BYTES:
        raise ChatError('Attachment exceeds 15 MB limit.', 400)

    ext = os.path.splitext(file_obj.name or '')[1] or ''
    path = default_storage.save(f'chat_attachments/{uuid.uuid4().hex}{ext}', file_obj)
    media_path = f'{settings.MEDIA_URL.rstrip("/")}/{path}'
    if not media_path.startswith('/'):
        media_path = f'/{media_path}'
    url = _absolute_file_url(media_path, request=request)
    return path, url, file_obj.name or 'file', content_type, size


def create_message(room, sender, body='', files=None, request=None):
    files = files or []
    body = (body or '').strip()

    if not body and not files:
        raise ChatError('Message body or at least one attachment is required.', 400)

    if files and body:
        message_type = ChatMessage.MESSAGE_TYPE_MIXED
    elif files:
        message_type = ChatMessage.MESSAGE_TYPE_ATTACHMENT
    else:
        message_type = ChatMessage.MESSAGE_TYPE_TEXT

    with transaction.atomic():
        message = ChatMessage.objects.create(
            room=room,
            sender=sender,
            body=body,
            message_type=message_type,
            status=ChatMessage.STATUS_SENT,
        )
        attachment_rows = []
        for file_obj in files:
            stored_path, url, original_name, content_type, size = _save_uploaded_file(
                file_obj, request=request
            )
            att = ChatAttachment.objects.create(
                message=message,
                file=stored_path,
                original_name=original_name,
                content_type=content_type,
                file_size=size,
            )
            attachment_rows.append((att, url))

        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])

    return message, attachment_rows


def notify_recipient_of_chat_message(room, sender, message):
    """Create in-app inbox (+ optional FCM) for the other participant."""
    other = room.other_user(sender)
    if not other:
        return None

    from notifications.models import NotificationType
    from notifications.inbox_service import create_inbox_notification

    body = (message.body or '').strip()
    if not body:
        body = 'Sent an attachment'
    else:
        body = body[:160]

    sender_name = (getattr(sender, 'full_name', None) or '').strip() or getattr(sender, 'email', 'Someone')
    return create_inbox_notification(
        user=other,
        notification_type=NotificationType.NEW_CHAT_MESSAGE,
        title=f'New message from {sender_name}',
        body=body,
        data={
            'room_id': room.id,
            'message_id': message.id,
            'billboard_id': room.billboard_id,
            'sender_id': sender.id,
        },
        related_object_type='chatmessage',
        related_object_id=message.id,
    )


def mark_message_delivered(message, recipient):
    if message.sender_id == recipient.id:
        return message
    if message.status == ChatMessage.STATUS_SENT:
        message.status = ChatMessage.STATUS_DELIVERED
        message.save(update_fields=['status'])
    return message


def mark_messages_seen(room, user, up_to_message_id):
    if not room.is_participant(user):
        raise ChatError('You are not a participant in this chat room.', 403)

    try:
        last_message = ChatMessage.objects.get(pk=up_to_message_id, room=room)
    except ChatMessage.DoesNotExist as exc:
        raise ChatError('Message not found in this room.', 404) from exc

    participant, _ = ChatRoomParticipant.objects.get_or_create(room=room, user=user)
    participant.last_read_message = last_message
    participant.last_read_at = timezone.now()
    participant.save(update_fields=['last_read_message', 'last_read_at'])

    # Mark incoming messages as seen (not own messages)
    ChatMessage.objects.filter(
        room=room,
        created_at__lte=last_message.created_at,
    ).exclude(sender=user).exclude(status=ChatMessage.STATUS_SEEN).update(
        status=ChatMessage.STATUS_SEEN
    )

    return last_message


def serialize_message(message, request=None):
    attachments = []
    for att in message.attachments.all():
        file_url = _absolute_file_url(att.file.url, request=request)
        attachments.append({
            'id': att.id,
            'original_name': att.original_name,
            'content_type': att.content_type,
            'file_size': att.file_size,
            'url': file_url,
        })

    return {
        'id': message.id,
        'room_id': message.room_id,
        'sender_id': message.sender_id,
        'sender_email': message.sender.email,
        'sender_name': message.sender.full_name or message.sender.email,
        'body': message.body,
        'message_type': message.message_type,
        'status': message.status,
        'attachments': attachments,
        'created_at': message.created_at.isoformat(),
    }


def get_room_unread_count(room, user):
    """Count messages in room not sent by user and not yet read by user."""
    unread_qs = ChatMessage.objects.filter(room=room).exclude(sender=user)
    participant = ChatRoomParticipant.objects.filter(room=room, user=user).first()
    if participant and participant.last_read_message_id:
        unread_qs = unread_qs.filter(created_at__gt=participant.last_read_message.created_at)
    return unread_qs.count()


def get_unread_summary(user):
    """Badge summary for advertiser and media owner inbox tabs."""
    rooms = list_rooms_for_user(user).only('id')
    by_room = []
    total = 0
    for room in rooms:
        count = get_room_unread_count(room, user)
        total += count
        if count > 0:
            by_room.append({'room_id': room.id, 'unread_count': count})
    return {
        'total_unread': total,
        'rooms_with_unread': len(by_room),
        'rooms': by_room,
    }


def serialize_room(room, user, request=None):
    other = room.other_user(user)
    last_message = (
        ChatMessage.objects.filter(room=room)
        .select_related('sender')
        .prefetch_related('attachments')
        .order_by('-created_at')
        .first()
    )
    unread_count = get_room_unread_count(room, user)

    billboard = room.billboard
    image = (billboard.images or [None])[0] if billboard.images else None

    return {
        'id': room.id,
        'billboard_id': room.billboard_id,
        'billboard': {
            'id': billboard.id,
            'city': billboard.city,
            'road_name': billboard.road_name,
            'ooh_media_type': billboard.ooh_media_type,
            'image': image,
        },
        'advertiser_id': room.advertiser_id,
        'media_owner_id': room.media_owner_id,
        'other_user': {
            'id': other.id if other else None,
            'email': other.email if other else None,
            'full_name': (other.full_name or other.email) if other else None,
            'user_type': other.user_type if other else None,
        },
        'last_message': serialize_message(last_message, request) if last_message else None,
        'unread_count': unread_count,
        'created_at': room.created_at.isoformat(),
        'updated_at': room.updated_at.isoformat(),
    }
