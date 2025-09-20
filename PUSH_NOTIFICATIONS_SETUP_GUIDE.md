# Push Notifications Setup Guide for ReachToLet Backend

This guide will help you set up Firebase Cloud Messaging (FCM) for push notifications in your ReachToLet backend.

## 🚀 Overview

The notification system includes:
- **Automatic notifications** for new leads, views, wishlist additions
- **User preferences** for notification types and quiet hours
- **Device token management** for multiple devices per user
- **Admin interface** for sending custom notifications
- **Analytics and tracking** for notification delivery and engagement

## 📋 Prerequisites

1. **Firebase Project**: Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. **Service Account Key**: Download your Firebase service account JSON file
3. **Mobile App**: Your Flutter/React Native app should be configured for FCM

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
pip install firebase-admin==6.4.0
```

### 2. Firebase Configuration

1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project or select existing one
   - Enable Cloud Messaging

2. **Download Service Account Key**:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file securely

3. **Update Django Settings**:
   ```python
   # In core/settings.py
   FIREBASE_CREDENTIALS_PATH = 'path/to/your/serviceAccountKey.json'
   ```

### 3. Database Migration

```bash
python manage.py makemigrations notifications
python manage.py migrate
```

### 4. Create Notification Templates (Optional)

```python
# Run in Django shell
from notifications.models import NotificationTemplate, NotificationType

# New Lead Template
NotificationTemplate.objects.create(
    name='New Lead Notification',
    notification_type=NotificationType.NEW_LEAD,
    title_template='New Lead! 🎉',
    body_template='Someone showed interest in your billboard in {city}',
    data_template={'billboard_id': '{billboard_id}', 'city': '{city}'}
)

# New View Template
NotificationTemplate.objects.create(
    name='View Milestone',
    notification_type=NotificationType.NEW_VIEW,
    title_template='Views Milestone! 👀',
    body_template='Your billboard in {city} reached {views} views!',
    data_template={'billboard_id': '{billboard_id}', 'views': '{views}'}
)
```

## 📱 Mobile App Integration

### Flutter Example

```dart
// 1. Add dependencies to pubspec.yaml
dependencies:
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.10

// 2. Initialize Firebase
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(MyApp());
}

// 3. Get FCM token and register with backend
class NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  
  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      // Get token
      String? token = await _messaging.getToken();
      if (token != null) {
        await registerDeviceToken(token);
      }
      
      // Listen for token refresh
      _messaging.onTokenRefresh.listen((newToken) {
        registerDeviceToken(newToken);
      });
    }
  }
  
  Future<void> registerDeviceToken(String token) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/notifications/device-token/register/'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'fcm_token': token,
          'device_type': Platform.isIOS ? 'ios' : 'android',
          'device_id': await getDeviceId(),
          'app_version': appVersion,
          'os_version': osVersion,
        }),
      );
      
      if (response.statusCode == 201) {
        print('Device token registered successfully');
      }
    } catch (e) {
      print('Failed to register device token: $e');
    }
  }
}

// 4. Handle incoming notifications
class NotificationHandler {
  void initialize() {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      // Handle foreground messages
      showNotification(message);
    });
    
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      // Handle background/terminated app messages
      handleNotificationTap(message);
    });
  }
  
  void showNotification(RemoteMessage message) {
    // Show local notification
    FlutterLocalNotificationsPlugin().show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          'default',
          'Default Channel',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
    );
  }
  
  void handleNotificationTap(RemoteMessage message) {
    // Navigate to specific screen based on notification data
    final data = message.data;
    if (data['billboard_id'] != null) {
      // Navigate to billboard details
      Navigator.pushNamed(context, '/billboard/${data['billboard_id']}');
    }
  }
}
```

### React Native Example

```javascript
// 1. Install dependencies
npm install @react-native-firebase/app @react-native-firebase/messaging

// 2. Initialize and register device
import messaging from '@react-native-firebase/messaging';

class NotificationService {
  async requestUserPermission() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log('Authorization status:', authStatus);
      await this.registerDevice();
    }
  }

  async registerDevice() {
    const token = await messaging().getToken();
    if (token) {
      await this.sendTokenToServer(token);
    }

    // Listen for token refresh
    messaging().onTokenRefresh(token => {
      this.sendTokenToServer(token);
    });
  }

  async sendTokenToServer(token) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notifications/device-token/register/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fcm_token: token,
          device_type: Platform.OS,
          device_id: DeviceInfo.getUniqueId(),
          app_version: DeviceInfo.getVersion(),
          os_version: DeviceInfo.getSystemVersion(),
        }),
      });
      
      if (response.ok) {
        console.log('Device token registered');
      }
    } catch (error) {
      console.error('Failed to register token:', error);
    }
  }
}
```

## 🔌 API Endpoints

### Device Token Management
- `POST /api/notifications/device-token/register/` - Register device token
- `POST /api/notifications/device-token/unregister/` - Unregister device token

### User Preferences
- `GET /api/notifications/preferences/` - Get notification preferences
- `PUT /api/notifications/preferences/` - Update notification preferences

### Notifications
- `GET /api/notifications/notifications/` - Get user notifications
- `POST /api/notifications/notifications/{id}/mark-opened/` - Mark notification as opened
- `POST /api/notifications/notifications/mark-all-opened/` - Mark all as opened

### Analytics
- `GET /api/notifications/stats/` - Get notification statistics
- `POST /api/notifications/test/` - Send test notification

### Admin (Admin Only)
- `POST /api/notifications/send/` - Send custom notification

## 📊 Example API Usage

### Register Device Token
```bash
curl -X POST http://localhost:8000/api/notifications/device-token/register/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "your_fcm_token_here",
    "device_type": "android",
    "device_id": "device_unique_id",
    "app_version": "1.0.0",
    "os_version": "Android 13"
  }'
```

### Update Notification Preferences
```bash
curl -X PUT http://localhost:8000/api/notifications/preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_leads_enabled": true,
    "new_views_enabled": false,
    "wishlist_updates_enabled": true,
    "push_enabled": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00:00",
    "quiet_hours_end": "08:00:00"
  }'
```

### Send Custom Notification (Admin)
```bash
curl -X POST http://localhost:8000/api/notifications/send/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "system_message",
    "title": "System Maintenance",
    "body": "We will be performing maintenance tonight at 2 AM",
    "all_users": true,
    "data": {
      "maintenance_time": "2024-01-15T02:00:00Z"
    }
  }'
```

## 🔄 Automatic Notifications

The system automatically sends notifications for:

1. **New Leads**: When someone shows interest in a billboard
2. **View Milestones**: Every 10 views (configurable)
3. **Wishlist Additions**: When someone adds a billboard to wishlist
4. **Billboard Status Changes**: When billboard is activated/deactivated

## 🛠️ Customization

### Adding New Notification Types

1. **Add to NotificationType choices**:
```python
# In notifications/models.py
class NotificationType(models.TextChoices):
    # ... existing types ...
    PRICE_UPDATE = 'price_update', 'Price Update'
    NEW_FEATURE = 'new_feature', 'New Feature'
```

2. **Create signal handler**:
```python
# In notifications/signals.py
@receiver(post_save, sender=YourModel)
def send_custom_notification(sender, instance, created, **kwargs):
    if created:
        push_service.send_notification(
            user=instance.user,
            notification_type=NotificationType.PRICE_UPDATE,
            title="Price Updated! 💰",
            body=f"Your billboard price has been updated",
            data={'billboard_id': str(instance.billboard.id)},
            content_object=instance.billboard
        )
```

### Custom Notification Templates

```python
# Create template in Django admin or via code
template = NotificationTemplate.objects.create(
    name='Custom Welcome',
    notification_type=NotificationType.WELCOME,
    title_template='Welcome to ReachToLet, {user_name}! 🎉',
    body_template='Start exploring billboards in {city}',
    data_template={'user_name': '{user_name}', 'city': '{city}'}
)
```

## 🐛 Troubleshooting

### Common Issues

1. **"FIREBASE_CREDENTIALS_PATH not set"**
   - Ensure you've set the path in settings.py
   - Verify the JSON file exists and is readable

2. **"Token unregistered"**
   - This is normal when users reinstall the app
   - Tokens are automatically deactivated

3. **Notifications not received**
   - Check user preferences
   - Verify device token is registered
   - Check quiet hours settings

4. **Firebase initialization error**
   - Verify service account key is valid
   - Check Firebase project configuration

### Debug Mode

Enable debug logging in settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'notifications': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📈 Analytics & Monitoring

The system tracks:
- **Delivery rates** per notification
- **Open rates** and engagement
- **Failed deliveries** with error messages
- **Device token validity**
- **User preferences** and opt-outs

Access analytics via Django admin or API endpoints.

## 🔒 Security Considerations

1. **Service Account Key**: Keep it secure and never commit to version control
2. **Token Validation**: Always validate user permissions before sending notifications
3. **Rate Limiting**: Implement rate limiting for notification endpoints
4. **Data Privacy**: Respect user preferences and quiet hours

## 🚀 Production Deployment

1. **Environment Variables**: Use environment variables for sensitive data
2. **Firebase Project**: Use production Firebase project
3. **Monitoring**: Set up monitoring for notification delivery rates
4. **Backup**: Regular backups of notification data
5. **Testing**: Test notifications in staging environment first

---

For more information, check the Django admin interface at `/admin/notifications/` to manage notifications, templates, and user preferences.
