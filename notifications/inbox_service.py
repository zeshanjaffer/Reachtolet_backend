"""In-app notification inbox helpers."""

from __future__ import annotations

import logging

from django.utils import timezone

from .models import NotificationPreference, NotificationType, UserNotification
from .services import push_service

logger = logging.getLogger(__name__)


def unread_count_for(user) -> int:
    return UserNotification.objects.filter(recipient=user, is_read=False).count()


def serialize_inbox_notification(notification: UserNotification) -> dict:
    return {
        'id': str(notification.id),
        'notification_type': notification.notification_type,
        'notification_type_display': notification.get_notification_type_display(),
        'title': notification.title,
        'body': notification.body,
        'data': notification.data or {},
        'related_object_type': notification.related_object_type or None,
        'related_object_id': notification.related_object_id,
        'is_read': notification.is_read,
        'read_at': notification.read_at.isoformat() if notification.read_at else None,
        'created_at': notification.created_at.isoformat() if notification.created_at else None,
    }


def create_inbox_notification(
    user,
    notification_type,
    title,
    body,
    data=None,
    related_object_type='',
    related_object_id=None,
    content_object=None,
    send_push=True,
):
    """
    Create an in-app inbox row and optionally send FCM push.

    Chat messages respect ``chat_messages_enabled`` (skip inbox + push when False).
    """
    if user is None:
        return None

    type_value = (
        notification_type.value
        if hasattr(notification_type, 'value')
        else str(notification_type)
    )

    if type_value == NotificationType.NEW_CHAT_MESSAGE:
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        if not prefs.chat_messages_enabled:
            logger.info('Chat inbox skipped for user %s — preference disabled', user.id)
            return None

    if content_object is not None and not related_object_type:
        related_object_type = content_object._meta.model_name
    if content_object is not None and related_object_id is None:
        related_object_id = content_object.pk

    try:
        notification = UserNotification.objects.create(
            recipient=user,
            notification_type=type_value,
            title=title,
            body=body,
            data=data or {},
            related_object_type=related_object_type or '',
            related_object_id=related_object_id,
        )
    except Exception as exc:
        logger.error('Failed to create inbox notification for user %s: %s', user.id, exc)
        return None

    if send_push:
        try:
            push_service.send_notification(
                user=user,
                notification_type=type_value,
                title=title,
                body=body,
                data=data or {},
                content_object=content_object,
            )
        except Exception as exc:
            logger.error('Push after inbox create failed for user %s: %s', user.id, exc)

    return notification


def mark_notification_read(notification: UserNotification) -> UserNotification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
    return notification


def mark_all_read(user) -> int:
    now = timezone.now()
    return UserNotification.objects.filter(recipient=user, is_read=False).update(
        is_read=True,
        read_at=now,
    )
