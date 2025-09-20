from rest_framework import serializers
from .models import (
    PushNotification, DeviceToken, NotificationPreference, 
    NotificationTemplate, NotificationType
)

class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer for device token registration"""
    class Meta:
        model = DeviceToken
        fields = [
            'fcm_token', 'device_type', 'device_id', 
            'app_version', 'os_version'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        return DeviceToken.objects.create(user=user, **validated_data)

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    class Meta:
        model = NotificationPreference
        fields = [
            'new_leads_enabled', 'new_views_enabled', 'wishlist_updates_enabled',
            'system_messages_enabled', 'push_enabled', 'sound_enabled',
            'vibration_enabled', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        return NotificationPreference.objects.create(user=user, **validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class PushNotificationSerializer(serializers.ModelSerializer):
    """Serializer for push notifications"""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    device_type_display = serializers.CharField(
        source='get_device_type_display', 
        read_only=True
    )
    
    class Meta:
        model = PushNotification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'title', 'body', 'device_type', 'device_type_display',
            'data', 'sent_at', 'delivered', 'delivered_at',
            'opened', 'opened_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'body', 'device_type',
            'data', 'sent_at', 'delivered', 'delivered_at',
            'opened', 'opened_at', 'error_message'
        ]

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display',
            'title_template', 'body_template', 'data_template', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending custom notifications"""
    notification_type = serializers.ChoiceField(choices=NotificationType.choices)
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    all_users = serializers.BooleanField(default=False)
    
    def validate(self, data):
        if not data.get('user_ids') and not data.get('all_users'):
            raise serializers.ValidationError(
                "Either user_ids or all_users must be specified"
            )
        return data
