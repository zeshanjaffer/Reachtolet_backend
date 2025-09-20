import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
from .models import PushNotification, DeviceToken, NotificationPreference, NotificationTemplate
import logging
import json

logger = logging.getLogger(__name__)

class PushNotificationService:
    """Service class for sending push notifications via Firebase Cloud Messaging"""
    
    def __init__(self):
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # You'll need to add your Firebase service account key to settings
                # FIREBASE_CREDENTIALS_PATH = 'path/to/your/serviceAccountKey.json'
                if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH'):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning("FIREBASE_CREDENTIALS_PATH not set in settings. Push notifications will not work.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
    
    def send_notification(self, user, notification_type, title, body, data=None, content_object=None):
        """
        Send push notification to a user
        
        Args:
            user: User object
            notification_type: Type of notification (from NotificationType choices)
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            content_object: Related object (e.g., billboard, lead)
        """
        try:
            # Check user preferences
            if not self._should_send_notification(user, notification_type):
                logger.info(f"Notification skipped for user {user.id} - preferences disabled")
                return None
            
            # Get user's device tokens
            device_tokens = DeviceToken.objects.filter(
                user=user,
                is_active=True
            )
            
            if not device_tokens.exists():
                logger.info(f"No active device tokens found for user {user.id}")
                return None
            
            notifications_sent = []
            
            for device_token in device_tokens:
                notification = self._create_notification_record(
                    user, notification_type, title, body, 
                    device_token.fcm_token, device_token.device_type,
                    data, content_object
                )
                
                # Send via FCM
                success = self._send_fcm_notification(notification, device_token)
                
                if success:
                    notifications_sent.append(notification)
                else:
                    # Mark as failed
                    notification.mark_as_failed("FCM send failed")
            
            return notifications_sent
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user.id}: {str(e)}")
            return None
    
    def send_notification_to_tokens(self, fcm_tokens, title, body, data=None, notification_type=None):
        """
        Send notification to specific FCM tokens (for bulk notifications)
        
        Args:
            fcm_tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data
            notification_type: Type of notification
        """
        try:
            if not fcm_tokens:
                return []
            
            # Prepare FCM message
            message = messaging.MulticastMessage(
                tokens=fcm_tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        priority='high',
                        channel_id='default'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send_multicast(message)
            
            logger.info(f"Sent {response.success_count} out of {len(fcm_tokens)} notifications")
            
            # Log failures
            if response.failure_count > 0:
                for idx, result in enumerate(response.responses):
                    if not result.success:
                        logger.error(f"Failed to send to token {fcm_tokens[idx]}: {result.exception}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {str(e)}")
            return None
    
    def _should_send_notification(self, user, notification_type):
        """Check if notification should be sent based on user preferences"""
        try:
            preferences, created = NotificationPreference.objects.get_or_create(user=user)
            
            # Check if push notifications are enabled
            if not preferences.push_enabled:
                return False
            
            # Check quiet hours
            if preferences.is_quiet_hours():
                return False
            
            # Check specific notification type preferences
            if notification_type == 'new_lead' and not preferences.new_leads_enabled:
                return False
            elif notification_type == 'new_view' and not preferences.new_views_enabled:
                return False
            elif notification_type == 'wishlist_added' and not preferences.wishlist_updates_enabled:
                return False
            elif notification_type == 'system_message' and not preferences.system_messages_enabled:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification preferences: {str(e)}")
            return True  # Default to sending if there's an error
    
    def _create_notification_record(self, user, notification_type, title, body, 
                                  fcm_token, device_type, data=None, content_object=None):
        """Create a notification record in the database"""
        notification = PushNotification.objects.create(
            recipient=user,
            notification_type=notification_type,
            title=title,
            body=body,
            fcm_token=fcm_token,
            device_type=device_type,
            data=data or {},
            content_type=content_object._meta if content_object else None,
            object_id=content_object.id if content_object else None
        )
        return notification
    
    def _send_fcm_notification(self, notification, device_token):
        """Send notification via Firebase Cloud Messaging"""
        try:
            # Prepare notification data
            notification_data = notification.data.copy()
            notification_data.update({
                'notification_id': str(notification.id),
                'notification_type': notification.notification_type,
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            })
            
            # Create FCM message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.body
                ),
                data=notification_data,
                token=device_token.fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default' if device_token.device_type == 'android' else None,
                        priority='high',
                        channel_id='default',
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default' if device_token.device_type == 'ios' else None,
                            badge=1,
                            alert=messaging.ApsAlert(
                                title=notification.title,
                                body=notification.body
                            )
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(message)
            
            # Mark as delivered
            notification.mark_as_delivered(response)
            
            logger.info(f"Successfully sent notification {notification.id} to {device_token.fcm_token[:20]}...")
            return True
            
        except messaging.UnregisteredError:
            # Token is invalid, deactivate it
            device_token.is_active = False
            device_token.save()
            notification.mark_as_failed("Token unregistered")
            logger.warning(f"Deactivated invalid token: {device_token.fcm_token[:20]}...")
            return False
            
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")
            return False
    
    def register_device_token(self, user, fcm_token, device_type='android', 
                            device_id=None, app_version=None, os_version=None):
        """Register or update a device token for a user"""
        try:
            device_token, created = DeviceToken.objects.update_or_create(
                fcm_token=fcm_token,
                defaults={
                    'user': user,
                    'device_type': device_type,
                    'device_id': device_id,
                    'app_version': app_version,
                    'os_version': os_version,
                    'is_active': True
                }
            )
            
            if created:
                logger.info(f"Registered new device token for user {user.id}")
            else:
                logger.info(f"Updated existing device token for user {user.id}")
            
            return device_token
            
        except Exception as e:
            logger.error(f"Error registering device token: {str(e)}")
            return None
    
    def unregister_device_token(self, fcm_token):
        """Unregister a device token"""
        try:
            DeviceToken.objects.filter(fcm_token=fcm_token).update(is_active=False)
            logger.info(f"Unregistered device token: {fcm_token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"Error unregistering device token: {str(e)}")
            return False
    
    def get_user_notifications(self, user, limit=50, offset=0):
        """Get notifications for a user"""
        return PushNotification.objects.filter(
            recipient=user
        ).order_by('-sent_at')[offset:offset + limit]
    
    def mark_notification_as_opened(self, notification_id):
        """Mark a notification as opened"""
        try:
            notification = PushNotification.objects.get(id=notification_id)
            notification.mark_as_opened()
            return True
        except PushNotification.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error marking notification as opened: {str(e)}")
            return False

# Global instance
push_service = PushNotificationService()
