from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    AdminNotificationCampaign,
    AdminNotificationRecipient,
    AdminNotificationTemplate,
    AdminNotificationAnalytics
)
from users.models import User
from notifications.models import DeviceToken

User = get_user_model()

class AdminNotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    usage_count = serializers.ReadOnlyField()
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = AdminNotificationTemplate
        fields = [
            'id', 'name', 'title', 'message', 'description',
            'recipient_type', 'variables', 'is_active',
            'usage_count', 'created_at', 'updated_at'
        ]

class AdminNotificationRecipientSerializer(serializers.ModelSerializer):
    """Serializer for notification recipients"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sent_at = serializers.DateTimeField(read_only=True)
    delivered_at = serializers.DateTimeField(read_only=True)
    opened_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = AdminNotificationRecipient
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_phone',
            'status', 'status_display', 'fcm_token', 'device_type',
            'message_id', 'sent_at', 'delivered_at', 'opened_at',
            'error_message', 'retry_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AdminNotificationAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for campaign analytics"""
    last_updated = serializers.ReadOnlyField()
    
    class Meta:
        model = AdminNotificationAnalytics
        fields = [
            'total_sent', 'total_delivered', 'total_opened', 'total_failed',
            'android_sent', 'ios_sent', 'web_sent',
            'delivery_rate', 'open_rate', 'failure_rate',
            'avg_delivery_time', 'peak_delivery_time', 'last_updated'
        ]

class AdminNotificationCampaignSerializer(serializers.ModelSerializer):
    """Serializer for notification campaigns"""
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recipient_type_display = serializers.CharField(source='get_recipient_type_display', read_only=True)
    
    # Related data
    recipients = AdminNotificationRecipientSerializer(many=True, read_only=True)
    analytics = AdminNotificationAnalyticsSerializer(read_only=True)
    
    # Computed fields
    recipient_count = serializers.SerializerMethodField()
    delivery_rate = serializers.SerializerMethodField()
    open_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminNotificationCampaign
        fields = [
            'id', 'title', 'message', 'recipient_type', 'recipient_type_display',
            'template_name', 'custom_data', 'status', 'status_display',
            'scheduled_at', 'sent_at', 'total_recipients', 'sent_count',
            'delivered_count', 'opened_count', 'failed_count',
            'created_by', 'created_by_name', 'created_by_email',
            'created_at', 'updated_at', 'recipients', 'analytics',
            'recipient_count', 'delivery_rate', 'open_rate'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sent_at',
            'total_recipients', 'sent_count', 'delivered_count',
            'opened_count', 'failed_count'
        ]
    
    def get_recipient_count(self, obj):
        """Get the number of recipients for this campaign"""
        return obj.recipients.count()
    
    def get_delivery_rate(self, obj):
        """Get delivery rate percentage"""
        if obj.sent_count > 0:
            return round((obj.delivered_count / obj.sent_count) * 100, 2)
        return 0.0
    
    def get_open_rate(self, obj):
        """Get open rate percentage"""
        if obj.delivered_count > 0:
            return round((obj.opened_count / obj.delivered_count) * 100, 2)
        return 0.0

class CreateNotificationCampaignSerializer(serializers.ModelSerializer):
    """Serializer for creating notification campaigns"""
    specific_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs for specific user targeting"
    )
    
    class Meta:
        model = AdminNotificationCampaign
        fields = [
            'title', 'message', 'recipient_type', 'template_name',
            'custom_data', 'scheduled_at', 'specific_user_ids'
        ]
    
    def validate(self, data):
        """Validate campaign data"""
        recipient_type = data.get('recipient_type')
        specific_user_ids = data.get('specific_user_ids', [])
        
        if recipient_type == 'specific_users' and not specific_user_ids:
            raise serializers.ValidationError({
                'specific_user_ids': 'User IDs are required when targeting specific users'
            })
        
        if recipient_type != 'specific_users' and specific_user_ids:
            raise serializers.ValidationError({
                'specific_user_ids': 'User IDs should only be provided for specific user targeting'
            })
        
        return data

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list in admin panel"""
    full_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    has_fcm_token = serializers.SerializerMethodField()
    last_login = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'full_name', 'phone', 'country_code',
            'user_type', 'has_fcm_token', 'is_active', 'date_joined',
            'last_login'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.name or obj.email
    
    def get_user_type(self, obj):
        """Determine user type based on billboards"""
        if obj.billboards.exists():
            return 'billboard_owner'
        elif obj.wishlist_items.exists():
            return 'advertiser'
        else:
            return 'user'
    
    def get_has_fcm_token(self, obj):
        """Check if user has active FCM token"""
        return obj.device_tokens.filter(is_active=True).exists()

class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_users = serializers.IntegerField()
    billboard_owners = serializers.IntegerField()
    advertisers = serializers.IntegerField()
    users_with_tokens = serializers.IntegerField()
    sent_today = serializers.IntegerField()
    sent_this_week = serializers.IntegerField()
    sent_this_month = serializers.IntegerField()
    
    # Campaign statistics
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    draft_campaigns = serializers.IntegerField()
    
    # Performance metrics
    avg_delivery_rate = serializers.FloatField()
    avg_open_rate = serializers.FloatField()

class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for bulk notification operations"""
    campaign_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=[
        ('send', 'Send'),
        ('cancel', 'Cancel'),
        ('retry_failed', 'Retry Failed'),
    ])
    
    def validate_campaign_id(self, value):
        """Validate campaign exists"""
        try:
            campaign = AdminNotificationCampaign.objects.get(id=value)
            if campaign.status not in ['draft', 'scheduled']:
                raise serializers.ValidationError(
                    f"Cannot perform action on campaign with status: {campaign.status}"
                )
            return value
        except AdminNotificationCampaign.DoesNotExist:
            raise serializers.ValidationError("Campaign not found")
