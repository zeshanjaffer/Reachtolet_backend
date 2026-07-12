from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import F
from django.conf import settings
from django.utils import timezone

from .geo_utils import sync_billboard_location


class OohMediaType(models.Model):
    """Catalog of OOH media / billboard types for create-billboard picker."""

    CATEGORY_DIGITAL = 'digital'
    CATEGORY_STATIC = 'static'
    CATEGORY_PLACE = 'place'
    CATEGORY_TRANSIT = 'transit'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_DIGITAL, 'Digital'),
        (CATEGORY_STATIC, 'Static'),
        (CATEGORY_PLACE, 'Place Based'),
        (CATEGORY_TRANSIT, 'Transit & Mobile'),
        (CATEGORY_OTHER, 'Other'),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )
    is_selectable = models.BooleanField(
        default=True,
        help_text='False for group headers like "All Digital" (picker only shows selectable types).',
    )
    is_digital = models.BooleanField(
        default=False,
        help_text='True = use digital specifications JSON form on create.',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'OOH media type'
        verbose_name_plural = 'OOH media types'

    def __str__(self):
        return self.name


class OohMediaTypeAttribute(models.Model):
    """Dynamic specification field definition for an OOH media type."""

    FIELD_TEXT = 'text'
    FIELD_NUMBER = 'number'
    FIELD_INTEGER = 'integer'
    FIELD_BOOLEAN = 'boolean'
    FIELD_SELECT = 'select'
    FIELD_MULTISELECT = 'multiselect'
    FIELD_TYPE_CHOICES = [
        (FIELD_TEXT, 'Text'),
        (FIELD_NUMBER, 'Number'),
        (FIELD_INTEGER, 'Integer'),
        (FIELD_BOOLEAN, 'Boolean'),
        (FIELD_SELECT, 'Select'),
        (FIELD_MULTISELECT, 'Multi-select'),
    ]

    media_type = models.ForeignKey(
        OohMediaType,
        on_delete=models.CASCADE,
        related_name='attributes',
    )
    key = models.SlugField(max_length=80)
    label = models.CharField(max_length=120)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    required = models.BooleanField(default=False)
    options = models.JSONField(null=True, blank=True)
    validation = models.JSONField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    help_text = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        unique_together = [('media_type', 'key')]
        verbose_name = 'OOH media type attribute'
        verbose_name_plural = 'OOH media type attributes'

    def __str__(self):
        return f'{self.media_type.slug}.{self.key}'


class Billboard(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='billboards', null=True, blank=True
    )
    city = models.CharField(max_length=100, db_index=True)  # Added index for filtering
    description = models.TextField(blank=True, null=True)
    number_of_boards = models.CharField(max_length=10, blank=True, null=True)
    average_daily_views = models.CharField(max_length=20, blank=True, null=True)
    traffic_direction = models.CharField(max_length=100, blank=True, null=True)
    road_position = models.CharField(max_length=100, blank=True, null=True)
    road_name = models.CharField(max_length=100, blank=True, null=True)
    exposure_time = models.CharField(max_length=100, blank=True, null=True)
    price_range = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        help_text='ISO 4217 currency code copied from owner preferred_currency on create',
    )
    display_height = models.CharField(max_length=20, blank=True, null=True)
    display_width = models.CharField(max_length=20, blank=True, null=True)
    advertiser_phone = models.CharField(max_length=20, blank=True, null=True)
    advertiser_whatsapp = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True, db_index=True)  # Added index for filtering
    company_website = models.CharField(max_length=200, blank=True, null=True)  # Changed from URLField to CharField
    ooh_media_type = models.CharField(max_length=100, db_index=True)  # synced from media_type.name
    media_type = models.ForeignKey(
        OohMediaType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='billboards',
    )
    ooh_media_id = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=50, db_index=True)  # Added index for filtering
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text='Type-specific config from frontend (digital slots, static pricing, etc.)',
    )
    unavailable_dates = models.JSONField(default=list, blank=True)
    latitude = models.FloatField(blank=True, null=True, db_index=True)  # Indexed for map queries
    longitude = models.FloatField(blank=True, null=True, db_index=True)  # Indexed for map queries
    location = gis_models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True,
        spatial_index=True,
        help_text='PostGIS geography point (synced from latitude/longitude)',
    )
    views = models.IntegerField(default=0)  # NEW: View count field
    leads = models.IntegerField(default=0, db_index=True)  # NEW: Simple leads counter
    is_active = models.BooleanField(default=True, db_index=True)  # NEW: Active/inactive toggle with index
    address = models.TextField(blank=True, null=True, help_text="Detailed address of the billboard location")
    generator_backup = models.CharField(
        max_length=3, 
        choices=[('Yes', 'Yes'), ('No', 'No')], 
        blank=True, 
        null=True,
        help_text="Whether the billboard has generator backup"
    )
    
    # Approval workflow fields
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending',
        help_text="Current approval status of the billboard",
        db_index=True
    )
    
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the billboard was approved"
    )
    
    rejected_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the billboard was rejected"
    )
    
    rejection_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Reason for rejection (if applicable)"
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_billboards',
        help_text="Admin user who approved this billboard"
    )
    
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_billboards',
        help_text="Admin user who rejected this billboard"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Added index for ordering

    def __str__(self):
        return f"{self.city} - {self.get_approval_status_display()}"

    def save(self, *args, **kwargs):
        if self.media_type_id:
            self.ooh_media_type = self.media_type.name
        sync_billboard_location(self)
        super().save(*args, **kwargs)

    def increment_views(self):
        """Increment the view count for this billboard (prefer billboards.tracking + F())."""
        Billboard.objects.filter(pk=self.pk).update(views=F('views') + 1)

    def increment_leads(self):
        """Increment the leads count for this billboard (prefer billboards.tracking + F())."""
        Billboard.objects.filter(pk=self.pk).update(leads=F('leads') + 1)
    
    def toggle_active(self):
        """Toggle the active status of the billboard"""
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])
        return self.is_active
    
    def approve(self, approved_by_user):
        """Approve the billboard"""
        # Store previous status for signal
        self._previous_approval_status = self.approval_status
        self.approval_status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = approved_by_user
        self.rejected_at = None
        self.rejected_by = None
        self.rejection_reason = None
        self.save(update_fields=['approval_status', 'approved_at', 'approved_by', 'rejected_at', 'rejected_by', 'rejection_reason'])
        return True
    
    def reject(self, rejected_by_user, rejection_reason=''):
        """Reject the billboard"""
        # Store previous status for signal
        self._previous_approval_status = self.approval_status
        self.approval_status = 'rejected'
        self.rejected_at = timezone.now()
        self.rejected_by = rejected_by_user
        self.rejection_reason = rejection_reason
        self.approved_at = None
        self.approved_by = None
        self.save(update_fields=['approval_status', 'rejected_at', 'rejected_by', 'rejection_reason', 'approved_at', 'approved_by'])
        # Cache will be invalidated by signal
        return True
    
    def is_approved(self):
        """Check if billboard is approved"""
        return self.approval_status == 'approved'
    
    def is_pending(self):
        """Check if billboard is pending approval"""
        return self.approval_status == 'pending'
    
    def is_rejected(self):
        """Check if billboard is rejected"""
        return self.approval_status == 'rejected'

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),  # Composite index for common query
            models.Index(fields=['user', 'is_active']),  # Composite index for user's billboards
            models.Index(fields=['city', 'is_active']),  # Composite index for city filtering
            models.Index(fields=['leads']),  # Index for lead analytics
            models.Index(fields=['approval_status']),  # Index for approval status filtering
            models.Index(fields=['approval_status', 'is_active']),  # Composite index for approved and active billboards
            models.Index(fields=['user', 'approval_status']),  # Composite index for user's billboards by status
            models.Index(fields=['latitude', 'longitude']),  # Index for map bounds queries (CRITICAL for performance)
            models.Index(fields=['approval_status', 'is_active', 'latitude', 'longitude']),  # Composite index for map queries
        ]


class Wishlist(models.Model):
    """Model to track user's saved billboards"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items'
    )
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'billboard']  # Prevent duplicate entries
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.billboard.city}"


class Lead(models.Model):
    """Model to track individual lead interactions per user per billboard"""
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='lead_interactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who clicked lead (if authenticated)"
    )
    user_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        help_text="Browser/device information"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billboard', 'user_ip']),
            models.Index(fields=['billboard', 'user']),
            models.Index(fields=['user_ip', 'created_at']),
            models.Index(fields=['billboard', 'user', 'created_at']),
        ]

    def __str__(self):
        user_info = self.user.email if self.user else f"IP {self.user_ip}"
        return f"{self.billboard.city} - Lead from {user_info} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class View(models.Model):
    """Model to track individual view interactions per user per billboard"""
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='view_interactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who viewed (if authenticated)"
    )
    user_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        help_text="Browser/device information"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billboard', 'user_ip']),
            models.Index(fields=['billboard', 'user']),
            models.Index(fields=['user_ip', 'created_at']),
            models.Index(fields=['billboard', 'user', 'created_at']),
        ]

    def __str__(self):
        user_info = self.user.email if self.user else f"IP {self.user_ip}"
        return f"{self.billboard.city} - View from {user_info} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"