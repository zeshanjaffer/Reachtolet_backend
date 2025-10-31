from django.contrib import admin
from .models import (
    AdminNotificationCampaign,
    AdminNotificationRecipient,
    AdminNotificationTemplate,
    AdminNotificationAnalytics
)

@admin.register(AdminNotificationCampaign)
class AdminNotificationCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient_type', 'status', 'total_recipients',
        'sent_count', 'delivered_count', 'opened_count', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'recipient_type', 'created_at']
    search_fields = ['title', 'message', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sent_at']
    fieldsets = (
        ('Campaign Details', {
            'fields': ('title', 'message', 'recipient_type', 'template_name')
        }),
        ('Settings', {
            'fields': ('custom_data', 'scheduled_at')
        }),
        ('Status & Statistics', {
            'fields': ('status', 'total_recipients', 'sent_count', 'delivered_count', 'opened_count', 'failed_count')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'sent_at')
        })
    )

@admin.register(AdminNotificationRecipient)
class AdminNotificationRecipientAdmin(admin.ModelAdmin):
    list_display = [
        'campaign', 'user', 'status', 'device_type', 'sent_at', 'delivered_at', 'opened_at'
    ]
    list_filter = ['status', 'device_type', 'campaign__recipient_type']
    search_fields = ['user__email', 'user__name', 'campaign__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AdminNotificationTemplate)
class AdminNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'recipient_type', 'is_active', 'usage_count', 'created_at']
    list_filter = ['recipient_type', 'is_active']
    search_fields = ['name', 'title', 'message']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']

@admin.register(AdminNotificationAnalytics)
class AdminNotificationAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'campaign', 'total_sent', 'total_delivered', 'total_opened',
        'delivery_rate', 'open_rate', 'last_updated'
    ]
    readonly_fields = [
        'total_sent', 'total_delivered', 'total_opened', 'total_failed',
        'android_sent', 'ios_sent', 'web_sent',
        'delivery_rate', 'open_rate', 'failure_rate',
        'avg_delivery_time', 'peak_delivery_time', 'last_updated'
    ]
