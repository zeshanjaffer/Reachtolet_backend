"""Booking business logic: overlap, calendar, status transitions."""

from __future__ import annotations

import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from billboards.availability_utils import normalize_booked_dates
from billboards.models import Billboard

from .models import Booking, BookingContent, Payment

PENDING_EXPIRY_HOURS = 48
# DecimalField(max_digits=12, decimal_places=2) → abs value < 10^10
_MAX_PRICE = Decimal('9999999999.99')
_PRICE_TOKEN_RE = re.compile(r'\d+(?:\.\d+)?')


class BookingError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def resolve_content_type(billboard: Billboard) -> str:
    """Map billboard media type → BookingContent.content_type."""
    mt = getattr(billboard, 'media_type', None)
    if mt is not None:
        if mt.is_digital or mt.category == 'digital':
            return BookingContent.CONTENT_DIGITAL
        return BookingContent.CONTENT_STATIC

    name = (billboard.ooh_media_type or '').lower()
    if 'digital' in name or 'led' in name or 'screen' in name:
        return BookingContent.CONTENT_DIGITAL
    return BookingContent.CONTENT_STATIC


def content_capabilities(billboard: Billboard) -> dict:
    content_type = resolve_content_type(billboard)
    digital = content_type == BookingContent.CONTENT_DIGITAL
    return {
        'content_type': content_type,
        'allows_in_app_media': digital,
        'requires_slot_timing': digital,
        'creative_hint': (
            'Upload MP4/JPG and optionally set daypart / duration.'
            if digital
            else 'Poster/print is handled offline. Share install notes and delivery plan with the media owner.'
        ),
    }


def _parse_price(billboard: Billboard):
    """Extract a storeable price from free-text price_range (e.g. '300000-50000')."""
    raw = (billboard.price_range or '').strip()
    if not raw:
        return None
    # Don't concatenate range ends ('300000-50000' → 30000050000 overflow).
    # Use the first numeric token as the booking quote.
    tokens = _PRICE_TOKEN_RE.findall(raw.replace(',', ''))
    if not tokens:
        return None
    try:
        value = Decimal(tokens[0])
    except (InvalidOperation, ValueError):
        return None
    if value > _MAX_PRICE:
        return None
    return value


def ranges_overlap(start_a, end_a, start_b, end_b) -> bool:
    return start_a <= end_b and end_a >= start_b


def find_overlapping_bookings(billboard_id, start_date, end_date, exclude_booking_id=None):
    qs = Booking.objects.filter(
        billboard_id=billboard_id,
        status__in=Booking.BLOCKING_STATUSES,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)
    return qs


def build_calendar_busy(billboard: Billboard, from_date=None, to_date=None) -> list[dict]:
    """Busy ranges for advertiser calendar (bookings + owner manual blocks)."""
    busy = []

    booking_qs = Booking.objects.filter(
        billboard=billboard,
        status__in=Booking.BLOCKING_STATUSES,
    )
    if from_date:
        booking_qs = booking_qs.filter(end_date__gte=from_date)
    if to_date:
        booking_qs = booking_qs.filter(start_date__lte=to_date)

    for b in booking_qs.only('id', 'start_date', 'end_date', 'status'):
        busy.append({
            'start': b.start_date.isoformat(),
            'end': b.end_date.isoformat(),
            'reason': 'booked' if b.status != Booking.STATUS_PENDING else 'pending_hold',
            'booking_id': b.id,
            'status': b.status,
        })

    # Owner manual day blocks (legacy unavailable_dates)
    for day in normalize_booked_dates(billboard.unavailable_dates or []):
        if from_date and day < from_date:
            continue
        if to_date and day > to_date:
            continue
        busy.append({
            'start': day,
            'end': day,
            'reason': 'owner_block',
            'booking_id': None,
            'status': None,
        })

    busy.sort(key=lambda x: (x['start'], x['end']))
    return busy


@transaction.atomic
def create_booking_request(advertiser, billboard_id, start_date, end_date, message=''):
    if advertiser.user_type != 'advertiser':
        raise BookingError('Only advertisers can request bookings.', 403)

    if end_date < start_date:
        raise BookingError('end_date must be on or after start_date.', 400)

    today = timezone.localdate()
    if start_date < today:
        raise BookingError('start_date cannot be in the past.', 400)

    # of=('self',): Postgres forbids FOR UPDATE on nullable outer joins
    # (user / media_type are null=True → LEFT OUTER JOIN via select_related).
    billboard = (
        Billboard.objects.select_for_update(of=('self',))
        .select_related('user', 'media_type')
        .filter(pk=billboard_id)
        .first()
    )
    if not billboard:
        raise BookingError('Billboard not found.', 404)

    if not billboard.is_active or billboard.approval_status != 'approved':
        raise BookingError('This billboard is not available for booking.', 400)

    if not billboard.user_id:
        raise BookingError('This billboard has no media owner.', 400)

    if billboard.user_id == advertiser.id:
        raise BookingError('You cannot book your own billboard.', 400)

    if find_overlapping_bookings(billboard.id, start_date, end_date).exists():
        raise BookingError('Selected dates overlap an existing booking or hold.', 409)

    booking = Booking.objects.create(
        billboard=billboard,
        advertiser=advertiser,
        media_owner=billboard.user,
        start_date=start_date,
        end_date=end_date,
        status=Booking.STATUS_PENDING,
        total_price=_parse_price(billboard),
        currency=(billboard.currency or advertiser.preferred_currency or 'PKR')[:3],
        advertiser_message=(message or '').strip(),
        expires_at=timezone.now() + timedelta(hours=PENDING_EXPIRY_HOURS),
    )
    Payment.objects.create(
        booking=booking,
        amount=booking.total_price,
        currency=booking.currency,
        status=Payment.STATUS_SKIPPED,
    )
    _notify_owner_new_request(booking)
    return booking


@transaction.atomic
def accept_booking(owner, booking_id, owner_note=''):
    booking = (
        Booking.objects.select_for_update(of=('self',))
        .select_related('billboard', 'billboard__media_type', 'advertiser', 'media_owner')
        .filter(pk=booking_id)
        .first()
    )
    if not booking:
        raise BookingError('Booking not found.', 404)
    if booking.media_owner_id != owner.id:
        raise BookingError('Only the media owner can accept this booking.', 403)
    if booking.status != Booking.STATUS_PENDING:
        raise BookingError(f'Cannot accept a booking in status "{booking.status}".', 400)

    if find_overlapping_bookings(
        booking.billboard_id,
        booking.start_date,
        booking.end_date,
        exclude_booking_id=booking.id,
    ).exists():
        raise BookingError('Dates are no longer available.', 409)

    booking.status = Booking.STATUS_ACCEPTED
    booking.owner_note = (owner_note or '').strip()
    booking.expires_at = None
    booking.save(update_fields=['status', 'owner_note', 'expires_at', 'updated_at'])

    content_type = resolve_content_type(booking.billboard)
    content, _ = BookingContent.objects.get_or_create(
        booking=booking,
        defaults={
            'content_type': content_type,
            'status': BookingContent.STATUS_AWAITING,
        },
    )

    # V1: payment skipped — leave Payment as skipped
    _notify_advertiser_accepted(booking)
    return booking, content


@transaction.atomic
def reject_booking(owner, booking_id, reason=''):
    booking = Booking.objects.select_for_update().filter(pk=booking_id).first()
    if not booking:
        raise BookingError('Booking not found.', 404)
    if booking.media_owner_id != owner.id:
        raise BookingError('Only the media owner can reject this booking.', 403)
    if booking.status != Booking.STATUS_PENDING:
        raise BookingError(f'Cannot reject a booking in status "{booking.status}".', 400)

    booking.status = Booking.STATUS_REJECTED
    booking.rejection_reason = (reason or '').strip() or 'Rejected by media owner'
    booking.expires_at = None
    booking.save(update_fields=['status', 'rejection_reason', 'expires_at', 'updated_at'])
    _notify_advertiser_rejected(booking)
    return booking


@transaction.atomic
def cancel_booking(user, booking_id):
    booking = Booking.objects.select_for_update().filter(pk=booking_id).first()
    if not booking:
        raise BookingError('Booking not found.', 404)

    is_adv = booking.advertiser_id == user.id
    is_owner = booking.media_owner_id == user.id
    if not is_adv and not is_owner:
        raise BookingError('You are not a participant in this booking.', 403)

    if booking.status not in (
        Booking.STATUS_PENDING,
        Booking.STATUS_ACCEPTED,
        Booking.STATUS_PAID,
    ):
        raise BookingError(f'Cannot cancel a booking in status "{booking.status}".', 400)

    booking.status = Booking.STATUS_CANCELLED
    booking.expires_at = None
    booking.save(update_fields=['status', 'expires_at', 'updated_at'])
    return booking


@transaction.atomic
def submit_content(advertiser, booking_id, *, data, media_file=None):
    booking = (
        Booking.objects.select_for_update(of=('self',))
        .select_related('content')
        .filter(pk=booking_id)
        .first()
    )
    if not booking:
        raise BookingError('Booking not found.', 404)
    if booking.advertiser_id != advertiser.id:
        raise BookingError('Only the advertiser can submit content.', 403)
    if booking.status not in (Booking.STATUS_ACCEPTED, Booking.STATUS_PAID, Booking.STATUS_CONFIRMED):
        raise BookingError('Content can only be submitted after the booking is accepted.', 400)

    content = getattr(booking, 'content', None)
    if content is None:
        content = BookingContent.objects.create(
            booking=booking,
            content_type=resolve_content_type(booking.billboard),
            status=BookingContent.STATUS_AWAITING,
        )

    if content.status == BookingContent.STATUS_OWNER_APPROVED:
        raise BookingError('Content is already approved.', 400)

    if content.content_type == BookingContent.CONTENT_DIGITAL:
        video_url = (data.get('video_url') or '').strip()
        if media_file:
            content.media_file = media_file
        if video_url:
            content.video_url = video_url
        if not content.media_file and not content.video_url:
            raise BookingError('Provide a media file or video_url for digital bookings.', 400)
        content.slot_daypart = (data.get('slot_daypart') or '').strip()
        duration = data.get('duration_seconds')
        if duration in (None, ''):
            content.duration_seconds = None
        else:
            try:
                content.duration_seconds = int(duration)
            except (TypeError, ValueError) as exc:
                raise BookingError('duration_seconds must be an integer.', 400) from exc
        content.digital_notes = (data.get('digital_notes') or '').strip()
    else:
        notes = (data.get('install_notes') or '').strip()
        if not notes:
            raise BookingError('install_notes is required for static bookings.', 400)
        content.install_notes = notes
        content.external_link = (data.get('external_link') or '').strip()

    content.status = BookingContent.STATUS_SUBMITTED
    content.submitted_at = timezone.now()
    content.owner_feedback = ''
    content.save()
    _notify_owner_content_submitted(booking)
    return content


@transaction.atomic
def approve_content(owner, booking_id, *, install_confirmed=False):
    booking = (
        Booking.objects.select_for_update(of=('self',))
        .select_related('content')
        .filter(pk=booking_id)
        .first()
    )
    if not booking:
        raise BookingError('Booking not found.', 404)
    if booking.media_owner_id != owner.id:
        raise BookingError('Only the media owner can approve content.', 403)

    content = getattr(booking, 'content', None)
    if content is None or content.status != BookingContent.STATUS_SUBMITTED:
        raise BookingError('No submitted content to approve.', 400)

    content.status = BookingContent.STATUS_OWNER_APPROVED
    content.reviewed_at = timezone.now()
    if content.content_type == BookingContent.CONTENT_STATIC and install_confirmed:
        content.install_confirmed_by_owner = True
    content.save()

    # V1: skip paid → confirmed (and live if already started)
    today = timezone.localdate()
    if booking.start_date <= today <= booking.end_date:
        booking.status = Booking.STATUS_LIVE
    elif booking.start_date > today:
        booking.status = Booking.STATUS_CONFIRMED
    else:
        booking.status = Booking.STATUS_COMPLETED
    booking.save(update_fields=['status', 'updated_at'])
    _notify_booking_confirmed(booking)
    return booking, content


@transaction.atomic
def reject_content(owner, booking_id, feedback=''):
    booking = (
        Booking.objects.select_for_update(of=('self',))
        .select_related('content')
        .filter(pk=booking_id)
        .first()
    )
    if not booking:
        raise BookingError('Booking not found.', 404)
    if booking.media_owner_id != owner.id:
        raise BookingError('Only the media owner can reject content.', 403)

    content = getattr(booking, 'content', None)
    if content is None or content.status != BookingContent.STATUS_SUBMITTED:
        raise BookingError('No submitted content to reject.', 400)

    content.status = BookingContent.STATUS_OWNER_REJECTED
    content.owner_feedback = (feedback or '').strip() or 'Please revise your creative.'
    content.reviewed_at = timezone.now()
    content.save()
    _notify_advertiser_content_rejected(booking, content)
    return content


def maybe_advance_live_and_completed():
    """Cron-friendly: confirmed→live, live→completed, expire pending."""
    today = timezone.localdate()
    now = timezone.now()

    Booking.objects.filter(
        status=Booking.STATUS_CONFIRMED,
        start_date__lte=today,
        end_date__gte=today,
    ).update(status=Booking.STATUS_LIVE, updated_at=now)

    Booking.objects.filter(
        status__in=(Booking.STATUS_CONFIRMED, Booking.STATUS_LIVE),
        end_date__lt=today,
    ).update(status=Booking.STATUS_COMPLETED, updated_at=now)

    Booking.objects.filter(
        status=Booking.STATUS_PENDING,
        expires_at__isnull=False,
        expires_at__lt=now,
    ).update(status=Booking.STATUS_CANCELLED, updated_at=now)


def _notify(user, ntype, title, body, booking):
    """Queue inbox/push after commit so a notify failure cannot roll back the booking."""
    user_id = getattr(user, 'id', None)
    booking_id = booking.id
    billboard_id = booking.billboard_id
    status_value = booking.status
    start_date = booking.start_date.isoformat()
    end_date = booking.end_date.isoformat()
    type_value = ntype

    def _send():
        try:
            from django.contrib.auth import get_user_model
            from notifications.inbox_service import create_inbox_notification

            recipient = get_user_model().objects.filter(pk=user_id).first()
            if recipient is None:
                return
            create_inbox_notification(
                user=recipient,
                notification_type=type_value,
                title=title,
                body=body,
                data={
                    'booking_id': booking_id,
                    'billboard_id': billboard_id,
                    'status': status_value,
                    'start_date': start_date,
                    'end_date': end_date,
                },
                related_object_type='booking',
                related_object_id=booking_id,
            )
        except Exception:
            pass

    transaction.on_commit(_send)


def _notify_owner_new_request(booking):
    from notifications.models import NotificationType

    _notify(
        booking.media_owner,
        NotificationType.BOOKING_REQUESTED,
        'New booking request',
        f'{booking.advertiser.full_name or booking.advertiser.email} requested '
        f'{booking.start_date} → {booking.end_date}.',
        booking,
    )


def _notify_advertiser_accepted(booking):
    from notifications.models import NotificationType

    _notify(
        booking.advertiser,
        NotificationType.BOOKING_ACCEPTED,
        'Booking accepted',
        'Your booking was accepted. Please submit your creative / install details.',
        booking,
    )


def _notify_advertiser_rejected(booking):
    from notifications.models import NotificationType

    _notify(
        booking.advertiser,
        NotificationType.BOOKING_REJECTED,
        'Booking rejected',
        booking.rejection_reason or 'Your booking request was rejected.',
        booking,
    )


def _notify_owner_content_submitted(booking):
    from notifications.models import NotificationType

    _notify(
        booking.media_owner,
        NotificationType.BOOKING_CONTENT_SUBMITTED,
        'Creative submitted',
        'The advertiser submitted content for review.',
        booking,
    )


def _notify_advertiser_content_rejected(booking, content):
    from notifications.models import NotificationType

    _notify(
        booking.advertiser,
        NotificationType.BOOKING_CONTENT_REJECTED,
        'Creative needs changes',
        content.owner_feedback or 'Please revise and resubmit your content.',
        booking,
    )


def _notify_booking_confirmed(booking):
    from notifications.models import NotificationType

    for user in (booking.advertiser, booking.media_owner):
        _notify(
            user,
            NotificationType.BOOKING_CONFIRMED,
            'Booking confirmed',
            f'Booking is now {booking.status} for {booking.start_date} → {booking.end_date}.',
            booking,
        )
