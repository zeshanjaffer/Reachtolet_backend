from django.conf import settings
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    """Inventory reservation for a billboard date range (hotel-style stay)."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_PAID = 'paid'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_LIVE = 'live'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_LIVE, 'Live'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Statuses that block the calendar for other advertisers
    BLOCKING_STATUSES = (
        STATUS_PENDING,
        STATUS_ACCEPTED,
        STATUS_PAID,
        STATUS_CONFIRMED,
        STATUS_LIVE,
    )

    billboard = models.ForeignKey(
        'billboards.Billboard',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    advertiser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advertiser_bookings',
    )
    media_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_bookings',
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=3, blank=True, default='')
    advertiser_message = models.TextField(blank=True, default='')
    rejection_reason = models.TextField(blank=True, default='')
    owner_note = models.TextField(blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billboard', 'status', 'start_date', 'end_date']),
            models.Index(fields=['advertiser', 'status']),
            models.Index(fields=['media_owner', 'status']),
        ]

    def __str__(self):
        return f'Booking #{self.pk} board={self.billboard_id} {self.start_date}→{self.end_date} ({self.status})'

    @property
    def is_blocking(self):
        return self.status in self.BLOCKING_STATUSES


class BookingContent(models.Model):
    """Creative / install package — created only after booking is accepted."""

    CONTENT_DIGITAL = 'digital'
    CONTENT_STATIC = 'static'
    CONTENT_TYPE_CHOICES = [
        (CONTENT_DIGITAL, 'Digital'),
        (CONTENT_STATIC, 'Static / physical'),
    ]

    STATUS_AWAITING = 'awaiting_input'
    STATUS_SUBMITTED = 'submitted'
    STATUS_OWNER_APPROVED = 'owner_approved'
    STATUS_OWNER_REJECTED = 'owner_rejected'
    STATUS_CHOICES = [
        (STATUS_AWAITING, 'Awaiting input'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_OWNER_APPROVED, 'Owner approved'),
        (STATUS_OWNER_REJECTED, 'Owner rejected'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='content',
    )
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AWAITING,
        db_index=True,
    )

    # Digital branch
    video_url = models.URLField(max_length=500, blank=True, default='')
    media_file = models.FileField(
        upload_to='booking_content/%Y/%m/',
        blank=True,
        null=True,
    )
    slot_daypart = models.CharField(max_length=100, blank=True, default='')
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    digital_notes = models.TextField(blank=True, default='')

    # Static / physical branch
    install_notes = models.TextField(blank=True, default='')
    install_confirmed_by_owner = models.BooleanField(default=False)
    external_link = models.URLField(max_length=500, blank=True, default='')

    owner_feedback = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking content'
        verbose_name_plural = 'Booking contents'

    def __str__(self):
        return f'Content for booking #{self.booking_id} ({self.content_type}/{self.status})'


class Payment(models.Model):
    """Payment stub — live gateway (JazzCash/Easypaisa) plugs in later."""

    STATUS_SKIPPED = 'skipped'
    STATUS_HELD = 'held'
    STATUS_CAPTURED = 'captured'
    STATUS_RELEASED = 'released'
    STATUS_REFUNDED = 'refunded'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_SKIPPED, 'Skipped (V1)'),
        (STATUS_HELD, 'Held'),
        (STATUS_CAPTURED, 'Captured'),
        (STATUS_RELEASED, 'Released to owner'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_FAILED, 'Failed'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SKIPPED,
        db_index=True,
    )
    gateway_ref = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Payment booking=#{self.booking_id} {self.status}'
