from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Device token management
    path('device-token/register/', views.DeviceTokenView.as_view(), name='register_device_token'),
    path('device-token/unregister/', views.UnregisterDeviceTokenView.as_view(), name='unregister_device_token'),
    
    # Notification preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification_preferences'),
    
    # In-app notification inbox
    path('inbox/unread-count/', views.InboxUnreadCountView.as_view(), name='inbox_unread_count'),
    path('inbox/mark-all-read/', views.InboxMarkAllReadView.as_view(), name='inbox_mark_all_read'),
    path('inbox/', views.InboxListView.as_view(), name='inbox_list'),
    path('inbox/<uuid:notification_id>/', views.InboxDetailView.as_view(), name='inbox_detail'),
    path('inbox/<uuid:notification_id>/read/', views.InboxMarkReadView.as_view(), name='inbox_mark_read'),

    # User notifications (legacy push history)
    path('notifications/', views.UserNotificationsView.as_view(), name='user_notifications'),
    path('notifications/<uuid:notification_id>/mark-opened/', views.mark_notification_opened, name='mark_notification_opened'),
    path('notifications/mark-all-opened/', views.mark_all_notifications_opened, name='mark_all_notifications_opened'),
    
    # Notification statistics
    path('stats/', views.NotificationStatsView.as_view(), name='notification_stats'),
    
    # Test notification
    path('test/', views.test_notification, name='test_notification'),
    
    # Admin endpoints
    path('send/', views.SendNotificationView.as_view(), name='send_notification'),
]
