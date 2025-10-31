from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class AdminNotificationCampaign(models.Model):
    """Model to track admin notification campaigns"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Campaign settings
    recipient_type = models.CharField(
        max_length=20,
        choices=[
            ('all_users', 'All Users'),
            ('billboard_owners', 'Billboard Owners Only'),
            ('advertisers', 'Advertisers Only'),
            ('specific_users', 'Specific Users'),
        ],
        default='all_users'
    )
    
    # Template settings
    template_name = models.CharField(max_length=100, blank=True, null=True)
    custom_data = models.JSONField(default=dict, blank=True)
    
    # Campaign status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='draft'
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_campaigns'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'admin_panel_notification_campaign'
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def mark_as_sent(self):
        """Mark campaign as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self):
        """Mark campaign as failed"""
        self.status = 'failed'
        self.save(update_fields=['status'])

class AdminNotificationRecipient(models.Model):
    """Model to track individual recipients of admin notifications"""
    campaign = models.ForeignKey(
        AdminNotificationCampaign,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_notification_recipients'
    )
    
    # Delivery tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('opened', 'Opened'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # FCM specific
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=10, blank=True, null=True)
    message_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['campaign', 'user']
        ordering = ['-created_at']
        db_table = 'admin_panel_notification_recipient'
    
    def __str__(self):
        return f"{self.campaign.title} - {self.user.email} - {self.get_status_display()}"

class AdminNotificationTemplate(models.Model):
    """Predefined templates for admin notifications"""
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    # Template settings
    recipient_type = models.CharField(
        max_length=20,
        choices=[
            ('all_users', 'All Users'),
            ('billboard_owners', 'Billboard Owners Only'),
            ('advertisers', 'Advertisers Only'),
            ('specific_users', 'Specific Users'),
        ],
        default='all_users'
    )
    
    # Template variables (for dynamic content)
    variables = models.JSONField(default=list, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        db_table = 'admin_panel_notification_template'
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

class AdminNotificationAnalytics(models.Model):
    """Analytics for admin notification campaigns"""
    campaign = models.OneToOneField(
        AdminNotificationCampaign,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Delivery metrics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    
    # Device breakdown
    android_sent = models.IntegerField(default=0)
    ios_sent = models.IntegerField(default=0)
    web_sent = models.IntegerField(default=0)
    
    # Time-based metrics
    delivery_rate = models.FloatField(default=0.0)
    open_rate = models.FloatField(default=0.0)
    failure_rate = models.FloatField(default=0.0)
    
    # Performance tracking
    avg_delivery_time = models.FloatField(default=0.0)  # in seconds
    peak_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Updated automatically
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_panel_notification_analytics'
    
    def __str__(self):
        return f"Analytics for {self.campaign.title}"
    
    def calculate_rates(self):
        """Calculate delivery and open rates"""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.open_rate = (self.total_opened / self.total_delivered) * 100 if self.total_delivered > 0 else 0
            self.failure_rate = (self.total_failed / self.total_sent) * 100
        self.save()
