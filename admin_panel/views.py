from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count, F
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import logging

from .models import (
    AdminNotificationCampaign,
    AdminNotificationRecipient,
    AdminNotificationTemplate,
    AdminNotificationAnalytics
)
from .serializers import (
    AdminNotificationCampaignSerializer,
    AdminNotificationTemplateSerializer,
    AdminNotificationRecipientSerializer,
    AdminNotificationAnalyticsSerializer,
    CreateNotificationCampaignSerializer,
    UserListSerializer,
    NotificationStatsSerializer,
    BulkNotificationSerializer
)
from notifications.models import DeviceToken, PushNotification
from notifications.services import PushNotificationService

User = get_user_model()
logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# ==================== CAMPAIGN MANAGEMENT ====================

class CampaignListCreateView(generics.ListCreateAPIView):
    """List and create notification campaigns"""
    queryset = AdminNotificationCampaign.objects.all()
    serializer_class = AdminNotificationCampaignSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter campaigns based on query parameters"""
        queryset = AdminNotificationCampaign.objects.select_related(
            'created_by'
        ).prefetch_related('recipients', 'analytics')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by recipient type
        recipient_type = self.request.query_params.get('recipient_type')
        if recipient_type:
            queryset = queryset.filter(recipient_type=recipient_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(message__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create campaign with current user as creator"""
        serializer.save(created_by=self.request.user)

class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific campaign"""
    queryset = AdminNotificationCampaign.objects.all()
    serializer_class = AdminNotificationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AdminNotificationCampaign.objects.select_related(
            'created_by'
        ).prefetch_related('recipients', 'analytics')

class CreateCampaignView(generics.CreateAPIView):
    """Create a new notification campaign with recipient targeting"""
    serializer_class = CreateNotificationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Create campaign and set up recipients"""
        campaign = serializer.save(created_by=self.request.user)
        
        # Set up recipients based on campaign type
        self._setup_recipients(campaign, serializer.validated_data)
        
        # Create analytics record
        AdminNotificationAnalytics.objects.create(campaign=campaign)
    
    def _setup_recipients(self, campaign, validated_data):
        """Set up recipients for the campaign"""
        recipient_type = campaign.recipient_type
        specific_user_ids = validated_data.get('specific_user_ids', [])
        
        if recipient_type == 'all_users':
            users = User.objects.filter(is_active=True)
        elif recipient_type == 'billboard_owners':
            users = User.objects.filter(
                is_active=True,
                billboards__isnull=False
            ).distinct()
        elif recipient_type == 'advertisers':
            users = User.objects.filter(
                is_active=True,
                wishlist_items__isnull=False
            ).distinct()
        elif recipient_type == 'specific_users':
            users = User.objects.filter(
                id__in=specific_user_ids,
                is_active=True
            )
        else:
            users = User.objects.none()
        
        # Create recipient records
        recipients = []
        for user in users:
            # Get user's active FCM tokens
            device_tokens = DeviceToken.objects.filter(
                user=user,
                is_active=True
            )
            
            if device_tokens.exists():
                for device_token in device_tokens:
                    recipient = AdminNotificationRecipient(
                        campaign=campaign,
                        user=user,
                        fcm_token=device_token.fcm_token,
                        device_type=device_token.device_type
                    )
                    recipients.append(recipient)
            else:
                # Create recipient without FCM token (will be skipped during sending)
                recipient = AdminNotificationRecipient(
                    campaign=campaign,
                    user=user
                )
                recipients.append(recipient)
        
        # Bulk create recipients
        if recipients:
            AdminNotificationRecipient.objects.bulk_create(recipients)
            campaign.total_recipients = len(recipients)
            campaign.save(update_fields=['total_recipients'])

# ==================== TEMPLATE MANAGEMENT ====================

class TemplateListCreateView(generics.ListCreateAPIView):
    """List and create notification templates"""
    queryset = AdminNotificationTemplate.objects.all()
    serializer_class = AdminNotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter active templates by default"""
        queryset = AdminNotificationTemplate.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')

class TemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific template"""
    queryset = AdminNotificationTemplate.objects.all()
    serializer_class = AdminNotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

# ==================== USER MANAGEMENT ====================

class UserListView(generics.ListAPIView):
    """List users for notification targeting"""
    serializer_class = UserListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on query parameters"""
        queryset = User.objects.filter(is_active=True).select_related().prefetch_related(
            'device_tokens', 'billboards', 'wishlist_items'
        )
        
        # Filter by user type
        user_type = self.request.query_params.get('user_type')
        if user_type == 'billboard_owners':
            queryset = queryset.filter(billboards__isnull=False).distinct()
        elif user_type == 'advertisers':
            queryset = queryset.filter(wishlist_items__isnull=False).distinct()
        
        # Filter by FCM token availability
        has_token = self.request.query_params.get('has_token')
        if has_token is not None:
            if has_token.lower() == 'true':
                queryset = queryset.filter(device_tokens__is_active=True).distinct()
            else:
                queryset = queryset.exclude(device_tokens__is_active=True)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset.order_by('-date_joined')

# ==================== NOTIFICATION SENDING ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_notification(request):
    """Send a notification campaign immediately"""
    try:
        campaign_id = request.data.get('campaign_id')
        if not campaign_id:
            return Response(
                {'error': 'Campaign ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            campaign = AdminNotificationCampaign.objects.get(id=campaign_id)
        except AdminNotificationCampaign.DoesNotExist:
            return Response(
                {'error': 'Campaign not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if campaign.status not in ['draft', 'scheduled']:
            return Response(
                {'error': f'Cannot send campaign with status: {campaign.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update campaign status
        campaign.status = 'sending'
        campaign.save(update_fields=['status'])
        
        # Send notifications
        success_count, failed_count = _send_campaign_notifications(campaign)
        
        # Update campaign statistics
        campaign.sent_count = success_count
        campaign.failed_count = failed_count
        campaign.mark_as_sent()
        
        return Response({
            'message': 'Notifications sent successfully',
            'sent_count': success_count,
            'failed_count': failed_count
        })
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
        return Response(
            {'error': 'Failed to send notifications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_notification_action(request):
    """Perform bulk actions on notifications"""
    serializer = BulkNotificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    campaign_id = serializer.validated_data['campaign_id']
    action = serializer.validated_data['action']
    
    try:
        campaign = AdminNotificationCampaign.objects.get(id=campaign_id)
        
        if action == 'send':
            campaign.status = 'sending'
            campaign.save(update_fields=['status'])
            success_count, failed_count = _send_campaign_notifications(campaign)
            campaign.sent_count = success_count
            campaign.failed_count = failed_count
            campaign.mark_as_sent()
            
            return Response({
                'message': 'Campaign sent successfully',
                'sent_count': success_count,
                'failed_count': failed_count
            })
        
        elif action == 'cancel':
            campaign.status = 'draft'
            campaign.save(update_fields=['status'])
            return Response({'message': 'Campaign cancelled successfully'})
        
        elif action == 'retry_failed':
            failed_recipients = campaign.recipients.filter(status='failed')
            success_count, failed_count = _send_campaign_notifications(
                campaign, failed_recipients
            )
            return Response({
                'message': 'Failed notifications retried',
                'sent_count': success_count,
                'failed_count': failed_count
            })
    
    except AdminNotificationCampaign.DoesNotExist:
        return Response(
            {'error': 'Campaign not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in bulk action: {str(e)}")
        return Response(
            {'error': 'Failed to perform action'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== ANALYTICS & STATISTICS ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for dashboard"""
    try:
        # User statistics
        total_users = User.objects.filter(is_active=True).count()
        billboard_owners = User.objects.filter(
            is_active=True,
            billboards__isnull=False
        ).distinct().count()
        advertisers = User.objects.filter(
            is_active=True,
            wishlist_items__isnull=False
        ).distinct().count()
        users_with_tokens = User.objects.filter(
            device_tokens__is_active=True
        ).distinct().count()
        
        # Notification statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        sent_today = AdminNotificationCampaign.objects.filter(
            sent_at__date=today
        ).aggregate(total=Count('id'))['total'] or 0
        
        sent_this_week = AdminNotificationCampaign.objects.filter(
            sent_at__date__gte=week_ago
        ).aggregate(total=Count('id'))['total'] or 0
        
        sent_this_month = AdminNotificationCampaign.objects.filter(
            sent_at__date__gte=month_ago
        ).aggregate(total=Count('id'))['total'] or 0
        
        # Campaign statistics
        total_campaigns = AdminNotificationCampaign.objects.count()
        active_campaigns = AdminNotificationCampaign.objects.filter(
            status__in=['sending', 'scheduled']
        ).count()
        draft_campaigns = AdminNotificationCampaign.objects.filter(
            status='draft'
        ).count()
        
        # Performance metrics
        from django.db.models import Avg
        analytics = AdminNotificationAnalytics.objects.all()
        avg_delivery_rate = analytics.aggregate(
            avg=Avg('delivery_rate')
        )['avg'] or 0.0
        avg_open_rate = analytics.aggregate(
            avg=Avg('open_rate')
        )['avg'] or 0.0
        
        stats = {
            'total_users': total_users,
            'billboard_owners': billboard_owners,
            'advertisers': advertisers,
            'users_with_tokens': users_with_tokens,
            'sent_today': sent_today,
            'sent_this_week': sent_this_week,
            'sent_this_month': sent_this_month,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'draft_campaigns': draft_campaigns,
            'avg_delivery_rate': round(avg_delivery_rate, 2),
            'avg_open_rate': round(avg_open_rate, 2)
        }
        
        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        return Response(
            {'error': 'Failed to get statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def campaign_analytics(request, campaign_id):
    """Get detailed analytics for a specific campaign"""
    try:
        campaign = AdminNotificationCampaign.objects.get(id=campaign_id)
        analytics = campaign.analytics
        
        if not analytics:
            analytics = AdminNotificationAnalytics.objects.create(campaign=campaign)
        
        serializer = AdminNotificationAnalyticsSerializer(analytics)
        return Response(serializer.data)
        
    except AdminNotificationCampaign.DoesNotExist:
        return Response(
            {'error': 'Campaign not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {str(e)}")
        return Response(
            {'error': 'Failed to get analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==================== HELPER FUNCTIONS ====================

def _send_campaign_notifications(campaign, recipients=None):
    """Send notifications for a campaign"""
    if recipients is None:
        recipients = campaign.recipients.filter(
            status='pending',
            fcm_token__isnull=False
        )
    
    success_count = 0
    failed_count = 0
    
    push_service = PushNotificationService()
    
    for recipient in recipients:
        try:
            # Send notification via FCM using the existing service
            notifications_sent = push_service.send_notification(
                user=recipient.user,
                notification_type='system_message',
                title=campaign.title,
                body=campaign.message,
                data=campaign.custom_data
            )
            
            if notifications_sent:
                recipient.status = 'sent'
                recipient.sent_at = timezone.now()
                recipient.message_id = notifications_sent[0].message_id if notifications_sent[0].message_id else None
                success_count += 1
            else:
                recipient.status = 'failed'
                recipient.error_message = "No active device tokens or notification preferences disabled"
                failed_count += 1
            
            recipient.save()
            
        except Exception as e:
            logger.error(f"Error sending notification to {recipient.user.email}: {str(e)}")
            recipient.status = 'failed'
            recipient.error_message = str(e)
            recipient.save()
            failed_count += 1
    
    # Update campaign analytics
    if hasattr(campaign, 'analytics'):
        analytics = campaign.analytics
        analytics.total_sent += success_count
        analytics.total_failed += failed_count
        analytics.calculate_rates()
    
    return success_count, failed_count

# ==================== ADMIN AUTHENTICATION ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Admin login endpoint for Next.js admin panel
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is staff (admin)
        if not user.is_staff:
            return Response({
                'error': 'Access denied. Admin privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name or user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return Response({
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user info
    """
    try:
        user = request.user
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name or user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return Response({
            'error': 'Failed to get user info'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_logout(request):
    """
    Admin logout endpoint
    """
    try:
        # In JWT, logout is typically handled client-side by removing tokens
        # But we can add any server-side cleanup here if needed
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Admin logout error: {str(e)}")
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
