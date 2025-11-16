from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import (
    PushNotification, DeviceToken, NotificationPreference, 
    NotificationTemplate, NotificationType
)
from .serializers import (
    DeviceTokenSerializer, NotificationPreferenceSerializer,
    PushNotificationSerializer, NotificationTemplateSerializer,
    SendNotificationSerializer
)
from .services import push_service
from core.pagination import CustomPagination
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

class DeviceTokenView(generics.CreateAPIView):
    """
    Register or update device token for push notifications.
    Required for receiving push notifications on mobile devices.
    """
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Register device token",
        operation_description="Register FCM device token for push notifications",
        tags=['Notifications'],
        security=[{'Bearer': []}],
        request_body=DeviceTokenSerializer,
        responses={201: 'Device token registered successfully'}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
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
            return Response({
                'message': 'Device token registered successfully',
                'device_token': DeviceTokenSerializer(device_token).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to register device token'
            }, status=status.HTTP_400_BAD_REQUEST)

class UnregisterDeviceTokenView(APIView):
    """Unregister device token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({
                'error': 'FCM token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = push_service.unregister_device_token(fcm_token)
        
        if success:
            return Response({
                'message': 'Device token unregistered successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to unregister device token'
            }, status=status.HTTP_400_BAD_REQUEST)

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get and update notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return NotificationPreference.objects.get_or_create(user=self.request.user)[0]

class UserNotificationsView(generics.ListAPIView):
    """
    Get user's notifications.
    Returns paginated list of push notifications for the authenticated user.
    """
    serializer_class = PushNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    @swagger_auto_schema(
        operation_summary="Get my notifications",
        tags=['Notifications'],
        security=[{'Bearer': []}],
        responses={200: PushNotificationSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return push_service.get_user_notifications(
            user=self.request.user,
            limit=self.request.query_params.get('limit', 50),
            offset=self.request.query_params.get('offset', 0)
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Mark notification as opened",
    tags=['Notifications'],
    security=[{'Bearer': []}],
    responses={200: 'Notification marked as opened', 400: 'Failed to mark notification'}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_opened(request, notification_id):
    """Mark a notification as opened"""
    success = push_service.mark_notification_as_opened(notification_id)
    
    if success:
        return Response({
            'message': 'Notification marked as opened'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Failed to mark notification as opened'
        }, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_summary="Mark all notifications as opened",
    tags=['Notifications'],
    security=[{'Bearer': []}],
    responses={200: 'All notifications marked as opened'}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_opened(request):
    """Mark all user notifications as opened"""
    try:
        PushNotification.objects.filter(
            recipient=request.user,
            opened=False
        ).update(opened=True, opened_at=timezone.now())
        
        return Response({
            'message': 'All notifications marked as opened'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error marking all notifications as opened: {str(e)}")
        return Response({
            'error': 'Failed to mark notifications as opened'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendNotificationView(generics.CreateAPIView):
    """
    Send custom notification to users (admin only).
    Allows admins to send push notifications to specific users or all users.
    """
    serializer_class = SendNotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Send notification (Admin)",
        operation_description="Send a custom push notification. Admin only.",
        tags=['Admin - Notifications'],
        security=[{'Bearer': []}],
        request_body=SendNotificationSerializer,
        responses={201: 'Notification sent successfully', 403: 'Admin access required'}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
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
            return Response({
                'message': 'Test notification sent successfully',
                'notification_count': len(notification)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No active device tokens found. Please register your device first.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return Response({
            'error': 'Failed to send test notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
