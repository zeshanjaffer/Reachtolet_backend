"""Billboard view/lead tracking — atomic DB writes for Celery workers."""

from __future__ import annotations

import logging

from django.db import transaction
from django.db.models import F

from notifications.models import NotificationType
from notifications.services import push_service

from .models import Billboard, Lead, View

logger = logging.getLogger(__name__)

TRACK_OWNER_SKIP = 'owner_skip'
TRACK_DUPLICATE = 'duplicate'
TRACK_RECORDED = 'tracked'
TRACK_NOT_FOUND = 'not_found'


def _interaction_exists(model, billboard_id, user_id, user_ip):
    if user_id:
        return model.objects.filter(billboard_id=billboard_id, user_id=user_id).exists()
    if user_ip:
        return model.objects.filter(billboard_id=billboard_id, user_ip=user_ip).exists()
    return False


def _send_lead_notification(billboard):
    if not billboard.user_id:
        return
    try:
        push_service.send_notification(
            user=billboard.user,
            notification_type=NotificationType.NEW_LEAD,
            title='New Lead! 🎉',
            body=f'Someone showed interest in your billboard in {billboard.city}',
            data={
                'billboard_id': str(billboard.id),
                'billboard_city': billboard.city,
                'lead_count': billboard.leads,
            },
            content_object=billboard,
        )
    except Exception as exc:
        logger.error('Lead notification failed for billboard %s: %s', billboard.id, exc)


def _send_view_milestone_notification(billboard, view_count):
    if not billboard.user_id or view_count <= 0 or view_count % 10 != 0:
        return
    try:
        push_service.send_notification(
            user=billboard.user,
            notification_type=NotificationType.NEW_VIEW,
            title='Views Milestone! 👀',
            body=f'Your billboard in {billboard.city} reached {view_count} views!',
            data={
                'billboard_id': str(billboard.id),
                'billboard_city': billboard.city,
                'view_count': view_count,
            },
            content_object=billboard,
        )
    except Exception as exc:
        logger.error('View milestone notification failed for billboard %s: %s', billboard.id, exc)


@transaction.atomic
def record_billboard_view(billboard_id, user_id=None, user_ip=None, user_agent=''):
    try:
        billboard = Billboard.objects.select_for_update().get(pk=billboard_id)
    except Billboard.DoesNotExist:
        return TRACK_NOT_FOUND

    if billboard.user_id and user_id and billboard.user_id == user_id:
        return TRACK_OWNER_SKIP

    if _interaction_exists(View, billboard_id, user_id, user_ip):
        return TRACK_DUPLICATE

    View.objects.create(
        billboard_id=billboard_id,
        user_id=user_id,
        user_ip=user_ip,
        user_agent=user_agent or '',
    )
    Billboard.objects.filter(pk=billboard_id).update(views=F('views') + 1)
    view_count = (
        Billboard.objects.filter(pk=billboard_id).values_list('views', flat=True).first()
    )
    billboard_for_notify = Billboard.objects.select_related('user').get(pk=billboard_id)
    _send_view_milestone_notification(billboard_for_notify, view_count or 0)
    return TRACK_RECORDED


@transaction.atomic
def record_billboard_lead(billboard_id, user_id=None, user_ip=None, user_agent=''):
    try:
        billboard = Billboard.objects.select_for_update().get(pk=billboard_id)
    except Billboard.DoesNotExist:
        return TRACK_NOT_FOUND

    if billboard.user_id and user_id and billboard.user_id == user_id:
        return TRACK_OWNER_SKIP

    if _interaction_exists(Lead, billboard_id, user_id, user_ip):
        return TRACK_DUPLICATE

    Lead.objects.create(
        billboard_id=billboard_id,
        user_id=user_id,
        user_ip=user_ip,
        user_agent=user_agent or '',
    )
    Billboard.objects.filter(pk=billboard_id).update(leads=F('leads') + 1)
    billboard_for_notify = Billboard.objects.select_related('user').get(pk=billboard_id)
    _send_lead_notification(billboard_for_notify)
    return TRACK_RECORDED
