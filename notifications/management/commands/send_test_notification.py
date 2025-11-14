"""
Django management command to send test notification to all users
Usage: python manage.py send_test_notification
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.services import push_service
from notifications.models import NotificationType, DeviceToken
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test notification to all users with registered device tokens'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting to send test notifications to all users...'))
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        total_users = users.count()
        self.stdout.write(f'📊 Found {total_users} active users')
        
        if total_users == 0:
            self.stdout.write(self.style.ERROR('❌ No active users found!'))
            return
        
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
                    self.stdout.write(self.style.WARNING(f'⚠️  User {user.email} has no active device tokens - skipping'))
                    continue
                
                users_with_tokens += 1
                
                # Send notification
                notification = push_service.send_notification(
                    user=user,
                    notification_type=NotificationType.SYSTEM_MESSAGE,
                    title='🧪 Test Notification - System Check',
                    body=f'Hello {user.name or user.email}! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅',
                    data={
                        'test': True,
                        'timestamp': timezone.now().isoformat(),
                        'message': 'Push notification system test'
                    }
                )
                
                if notification:
                    notifications_sent += len(notification)
                    self.stdout.write(self.style.SUCCESS(f'✅ Sent notification to {user.email} ({len(notification)} device(s))'))
                else:
                    notifications_failed += 1
                    self.stdout.write(self.style.ERROR(f'❌ Failed to send notification to {user.email}'))
                    
            except Exception as e:
                notifications_failed += 1
                self.stdout.write(self.style.ERROR(f'❌ Error sending to {user.email}: {str(e)}'))
        
        # Print summary
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Users with device tokens: {users_with_tokens}')
        self.stdout.write(f'Users without device tokens: {users_without_tokens}')
        self.stdout.write(self.style.SUCCESS(f'Notifications sent successfully: {notifications_sent}'))
        self.stdout.write(self.style.ERROR(f'Notifications failed: {notifications_failed}'))
        self.stdout.write('=' * 50)
        
        if notifications_sent > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Test notifications sent successfully!'))
            self.stdout.write('📱 Check your devices to see if you received the notification.')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  No notifications were sent.'))
            self.stdout.write('💡 Make sure:')
            self.stdout.write('   1. Users have registered their device tokens')
            self.stdout.write('   2. Firebase credentials are properly configured')
            self.stdout.write('   3. Device tokens are active')

