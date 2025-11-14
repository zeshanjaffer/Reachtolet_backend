# Django management command to send test notification
# Usage: python manage.py shell < send_notification_command.py

from django.contrib.auth import get_user_model
from notifications.services import push_service
from notifications.models import NotificationType, DeviceToken
from django.utils import timezone

User = get_user_model()

print("🚀 Starting to send test notifications to all users...")

# Get all active users
users = User.objects.filter(is_active=True)
total_users = users.count()
print(f"📊 Found {total_users} active users")

if total_users == 0:
    print("❌ No active users found!")
else:
    notifications_sent = 0
    notifications_failed = 0
    users_with_tokens = 0
    users_without_tokens = 0
    
    for user in users:
        try:
            # Check if user has device tokens
            device_tokens = DeviceToken.objects.filter(user=user, is_active=True)
            
            if not device_tokens.exists():
                users_without_tokens += 1
                print(f"⚠️  User {user.email} has no active device tokens - skipping")
                continue
            
            users_with_tokens += 1
            
            # Send notification
            notification = push_service.send_notification(
                user=user,
                notification_type=NotificationType.SYSTEM_MESSAGE,
                title="🧪 Test Notification - System Check",
                body=f"Hello {user.name or user.email}! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅",
                data={
                    'test': True,
                    'timestamp': timezone.now().isoformat(),
                    'message': 'Push notification system test'
                }
            )
            
            if notification:
                notifications_sent += len(notification)
                print(f"✅ Sent notification to {user.email} ({len(notification)} device(s))")
            else:
                notifications_failed += 1
                print(f"❌ Failed to send notification to {user.email}")
                
        except Exception as e:
            notifications_failed += 1
            print(f"❌ Error sending to {user.email}: {str(e)}")
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    print(f"Total users: {total_users}")
    print(f"Users with device tokens: {users_with_tokens}")
    print(f"Users without device tokens: {users_without_tokens}")
    print(f"Notifications sent successfully: {notifications_sent}")
    print(f"Notifications failed: {notifications_failed}")
    print("="*50)
    
    if notifications_sent > 0:
        print("\n✅ Test notifications sent successfully!")
        print("📱 Check your devices to see if you received the notification.")
    else:
        print("\n⚠️  No notifications were sent.")
        print("💡 Make sure:")
        print("   1. Users have registered their device tokens")
        print("   2. Firebase credentials are properly configured")
        print("   3. Device tokens are active")

