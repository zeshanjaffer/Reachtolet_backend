from django.contrib import admin
from .models import (
    PushNotification, DeviceToken, NotificationPreference, 
    NotificationTemplate, NotificationType
)

@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'notification_type', 'title', 
        'device_type', 'sent_at', 'delivered', 'opened'
    ]
    list_filter = [
        'notification_type', 'device_type', 'delivered', 'opened', 'sent_at'
    ]
    search_fields = ['recipient__email', 'recipient__username', 'title', 'body']
    readonly_fields = ['id', 'sent_at', 'delivered_at', 'opened_at']
    date_hierarchy = 'sent_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient')

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'device_type', 'device_id', 'app_version', 
        'os_version', 'is_active', 'created_at'
    ]
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__username', 'fcm_token', 'device_id']
    readonly_fields = ['created_at', 'last_used']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'push_enabled', 'new_leads_enabled', 'new_views_enabled',
        'wishlist_updates_enabled', 'system_messages_enabled'
    ]
    list_filter = [
        'push_enabled', 'new_leads_enabled', 'new_views_enabled',
        'wishlist_updates_enabled', 'system_messages_enabled'
    ]
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'notification_type', 'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['notification_type', 'is_active']
    search_fields = ['name', 'title_template', 'body_template']
    readonly_fields = ['created_at', 'updated_at']
