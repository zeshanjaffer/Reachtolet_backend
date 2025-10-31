from django.urls import path
from . import views

urlpatterns = [
    # Campaign Management
    path('admin/campaigns/', views.CampaignListCreateView.as_view(), name='admin-campaign-list-create'),
    path('admin/campaigns/<uuid:pk>/', views.CampaignDetailView.as_view(), name='admin-campaign-detail'),
    path('admin/campaigns/create/', views.CreateCampaignView.as_view(), name='admin-campaign-create'),
    
    # Template Management
    path('admin/templates/', views.TemplateListCreateView.as_view(), name='admin-template-list-create'),
    path('admin/templates/<int:pk>/', views.TemplateDetailView.as_view(), name='admin-template-detail'),
    
    # User Management
    path('admin/users/', views.UserListView.as_view(), name='admin-user-list'),
    
    # Notification Actions
    path('admin/send/', views.send_notification, name='admin-send-notification'),
    path('admin/bulk-action/', views.bulk_notification_action, name='admin-bulk-notification-action'),
    
    # Analytics & Statistics
    path('admin/stats/', views.notification_stats, name='admin-notification-stats'),
    path('admin/campaigns/<uuid:campaign_id>/analytics/', views.campaign_analytics, name='admin-campaign-analytics'),
]
