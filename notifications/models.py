from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import uuid

class NotificationType(models.TextChoices):
    """Types of notifications that can be sent"""
    NEW_LEAD = 'new_lead', 'New Lead'
    NEW_VIEW = 'new_view', 'New View'
    WISHLIST_ADDED = 'wishlist_added', 'Added to Wishlist'
    BILLBOARD_ACTIVATED = 'billboard_activated', 'Billboard Activated'
    BILLBOARD_DEACTIVATED = 'billboard_deactivated', 'Billboard Deactivated'
    PRICE_UPDATE = 'price_update', 'Price Update'
    SYSTEM_MESSAGE = 'system_message', 'System Message'
    WELCOME = 'welcome', 'Welcome Message'

class PushNotification(models.Model):
    """Model to track push notifications sent to mobile devices"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_notifications'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    
    # FCM specific fields
    fcm_token = models.CharField(max_length=255, db_index=True)
    device_type = models.CharField(
        max_length=10,
        choices=[
            ('ios', 'iOS'),
            ('android', 'Android'),
            ('web', 'Web'),
        ],
        default='android'
    )
    
    # Generic foreign key to link to any model (billboard, lead, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data for the notification
    data = models.JSONField(default=dict, blank=True)
    
    # FCM response tracking
    message_id = models.CharField(max_length=255, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['fcm_token', 'delivered']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.email} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_as_delivered(self, message_id=None):
        """Mark notification as delivered"""
        self.delivered = True
        self.delivered_at = timezone.now()
        if message_id:
            self.message_id = message_id
        self.save(update_fields=['delivered', 'delivered_at', 'message_id'])
    
    def mark_as_opened(self):
        """Mark notification as opened"""
        self.opened = True
        self.opened_at = timezone.now()
        self.save(update_fields=['opened', 'opened_at'])
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed"""
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['error_message', 'retry_count'])

class DeviceToken(models.Model):
    """Model to store FCM device tokens for users"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    fcm_token = models.CharField(max_length=255, unique=True, db_index=True)
    device_type = models.CharField(
        max_length=10,
        choices=[
            ('ios', 'iOS'),
            ('android', 'Android'),
            ('web', 'Web'),
        ],
        default='android'
    )
    device_id = models.CharField(max_length=255, blank=True, null=True)
    app_version = models.CharField(max_length=20, blank=True, null=True)
    os_version = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_device_token'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['fcm_token', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type} - {self.fcm_token[:20]}..."

class NotificationPreference(models.Model):
    """User preferences for push notifications"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Notification type preferences
    new_leads_enabled = models.BooleanField(default=True)
    new_views_enabled = models.BooleanField(default=True)
    wishlist_updates_enabled = models.BooleanField(default=True)
    system_messages_enabled = models.BooleanField(default=True)
    
    # General settings
    push_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    vibration_enabled = models.BooleanField(default=True)
    
    # Quiet hours (24-hour format)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_preference'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Quiet hours span midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end

class NotificationTemplate(models.Model):
    """Templates for different types of push notifications"""
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices
    )
    title_template = models.CharField(max_length=255)
    body_template = models.TextField()
    data_template = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification_template'
    
    def __str__(self):
        return f"{self.name} - {self.notification_type}"
