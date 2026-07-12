from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import (
    PushNotification, DeviceToken, NotificationPreference,
    NotificationTemplate, NotificationType, UserNotification
)
from .serializers import (
    DeviceTokenSerializer, NotificationPreferenceSerializer,
    PushNotificationSerializer, NotificationTemplateSerializer,
    SendNotificationSerializer
)
from .services import push_service
from .inbox_service import (
    unread_count_for,
    serialize_inbox_notification,
    mark_notification_read,
    mark_all_read,
)
from core.pagination import CustomPagination
from core.responses import action_response
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

class DeviceTokenView(generics.CreateAPIView):
    """Register or update device token for push notifications"""
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Register device token
        device_token = push_service.register_device_token(
            user=request.user,
            fcm_token=serializer.validated_data['fcm_token'],
            device_type=serializer.validated_data.get('device_type', 'android'),
            device_id=serializer.validated_data.get('device_id'),
            app_version=serializer.validated_data.get('app_version'),
            os_version=serializer.validated_data.get('os_version')
        )
        
        if device_token:
            return action_response('Device token registered successfully', status.HTTP_201_CREATED)
        return action_response('Failed to register device token', status.HTTP_400_BAD_REQUEST)

class UnregisterDeviceTokenView(APIView):
    """Unregister device token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return action_response('FCM token is required', status.HTTP_400_BAD_REQUEST)

        success = push_service.unregister_device_token(fcm_token)

        if success:
            return action_response('Device token unregistered successfully', status.HTTP_200_OK)
        return action_response('Failed to unregister device token', status.HTTP_400_BAD_REQUEST)

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get and update notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return NotificationPreference.objects.get_or_create(user=self.request.user)[0]

class UserNotificationsView(generics.ListAPIView):
    """Get user's notifications"""
    serializer_class = PushNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return push_service.get_user_notifications(
            user=self.request.user,
            limit=self.request.query_params.get('limit', 50),
            offset=self.request.query_params.get('offset', 0)
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_opened(request, notification_id):
    """Mark a notification as opened"""
    success = push_service.mark_notification_as_opened(notification_id)
    
    if success:
        return action_response('Notification marked as opened', status.HTTP_200_OK)
    return action_response('Failed to mark notification as opened', status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_opened(request):
    """Mark all user notifications as opened"""
    try:
        PushNotification.objects.filter(
            recipient=request.user,
            opened=False
        ).update(opened=True, opened_at=timezone.now())
        
        return action_response('All notifications marked as opened', status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error marking all notifications as opened: {str(e)}")
        return action_response('Failed to mark notifications as opened', status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendNotificationView(generics.CreateAPIView):
    """Send custom notification (admin only)"""
    serializer_class = SendNotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        notifications_sent = []
        
        try:
            if data.get('all_users'):
                # Send to all users
                users = User.objects.filter(is_active=True)
            else:
                # Send to specific users
                users = User.objects.filter(
                    id__in=data['user_ids'],
                    is_active=True
                )
            
            for user in users:
                notification = push_service.send_notification(
                    user=user,
                    notification_type=data['notification_type'],
                    title=data['title'],
                    body=data['body'],
                    data=data.get('data', {})
                )
                if notification:
                    notifications_sent.extend(notification)
            
            return Response({
                'message': f'Successfully sent {len(notifications_sent)} notifications',
                'notifications_sent': len(notifications_sent)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error sending custom notifications: {str(e)}")
            return Response({
                'error': 'Failed to send notifications'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationStatsView(APIView):
    """Get notification statistics for user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            total_notifications = PushNotification.objects.filter(
                recipient=request.user
            ).count()
            
            unread_notifications = PushNotification.objects.filter(
                recipient=request.user,
                opened=False
            ).count()
            
            delivered_notifications = PushNotification.objects.filter(
                recipient=request.user,
                delivered=True
            ).count()
            
            failed_notifications = PushNotification.objects.filter(
                recipient=request.user,
                error_message__isnull=False
            ).count()
            
            # Get recent notifications by type
            recent_by_type = {}
            for notification_type in NotificationType.values:
                count = PushNotification.objects.filter(
                    recipient=request.user,
                    notification_type=notification_type
                ).count()
                recent_by_type[notification_type] = count
            
            return Response({
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'delivered_notifications': delivered_notifications,
                'failed_notifications': failed_notifications,
                'notifications_by_type': recent_by_type
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            return Response({
                'error': 'Failed to get notification statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_notification(request):
    """Send a test notification to the current user"""
    try:
        notification = push_service.send_notification(
            user=request.user,
            notification_type=NotificationType.SYSTEM_MESSAGE,
            title="Test Notification 🔔",
            body="This is a test notification to verify your device is working properly!",
            data={
                'test': True,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        if notification:
            return action_response('Test notification sent successfully', status.HTTP_200_OK)
        return action_response(
            'No active device tokens found. Please register your device first.',
            status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return action_response('Failed to send test notification', status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── In-app notification inbox ───────────────────────────────────────────────

class InboxUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'status_code': status.HTTP_200_OK,
            'message': 'Unread count retrieved successfully',
            'unread_count': unread_count_for(request.user),
        }, status=status.HTTP_200_OK)


class InboxListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = UserNotification.objects.filter(recipient=request.user)

        is_read = request.query_params.get('is_read')
        if is_read is not None:
            val = str(is_read).strip().lower()
            if val in ('true', '1', 'yes'):
                qs = qs.filter(is_read=True)
            elif val in ('false', '0', 'no'):
                qs = qs.filter(is_read=False)

        notification_type = request.query_params.get('notification_type')
        if notification_type:
            qs = qs.filter(notification_type=notification_type)

        qs = qs.order_by('-created_at')

        try:
            page_size = int(request.query_params.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20
        page_size = max(1, min(page_size, 100))

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        page = paginator.paginate_queryset(qs, request)

        results = [serialize_inbox_notification(n) for n in page]
        return Response({
            'status_code': status.HTTP_200_OK,
            'message': 'Notifications retrieved successfully',
            'links': {
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
            },
            'count': paginator.page.paginator.count,
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number,
            'results': results,
            'unread_count': unread_count_for(request.user),
        }, status=status.HTTP_200_OK)


class InboxDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, notification_id):
        notification = get_object_or_404(
            UserNotification, id=notification_id, recipient=request.user
        )
        mark_read_param = request.query_params.get('mark_read', 'true')
        if str(mark_read_param).strip().lower() in ('true', '1', 'yes', ''):
            mark_notification_read(notification)
            notification.refresh_from_db()

        return Response({
            'status_code': status.HTTP_200_OK,
            'message': 'Notification retrieved successfully',
            'notification': serialize_inbox_notification(notification),
        }, status=status.HTTP_200_OK)


class InboxMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            UserNotification, id=notification_id, recipient=request.user
        )
        mark_notification_read(notification)
        notification.refresh_from_db()
        return Response({
            'status_code': status.HTTP_200_OK,
            'message': 'Notification marked as read',
            'notification': serialize_inbox_notification(notification),
            'unread_count': unread_count_for(request.user),
        }, status=status.HTTP_200_OK)


class InboxMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        marked_count = mark_all_read(request.user)
        return Response({
            'status_code': status.HTTP_200_OK,
            'message': 'All notifications marked as read',
            'marked_count': marked_count,
            'unread_count': unread_count_for(request.user),
        }, status=status.HTTP_200_OK)
