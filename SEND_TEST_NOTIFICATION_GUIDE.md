# How to Send Test Notification to All Users

## 🚀 Quick Method (Using API)

### **Option 1: Using the Script (Easiest)**

1. **Get your admin token:**
   ```bash
   # Login as admin
   curl -X POST http://localhost:8000/api/users/admin/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your_admin_email@example.com",
       "password": "your_admin_password"
     }'
   ```

2. **Copy the `access` token from the response**

3. **Update the script:**
   - Open `test_notification_api.py`
   - Replace `YOUR_ADMIN_TOKEN_HERE` with your actual token
   - Update `BASE_URL` if your server is on a different host/port

4. **Run the script:**
   ```bash
   python test_notification_api.py
   ```

### **Option 2: Using cURL Directly**

```bash
curl -X POST http://localhost:8000/api/notifications/send/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "system_message",
    "title": "🧪 Test Notification - System Check",
    "body": "Hello! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅",
    "all_users": true,
    "data": {
      "test": true,
      "message": "Push notification system test"
    }
  }'
```

### **Option 3: Using Django Shell**

```bash
python manage.py shell
```

Then paste this code:

```python
from django.contrib.auth import get_user_model
from notifications.services import push_service
from notifications.models import NotificationType
from django.utils import timezone

User = get_user_model()

# Get all active users
users = User.objects.filter(is_active=True)
print(f"Found {users.count()} active users")

notifications_sent = 0
for user in users:
    notification = push_service.send_notification(
        user=user,
        notification_type=NotificationType.SYSTEM_MESSAGE,
        title="🧪 Test Notification - System Check",
        body=f"Hello {user.name or user.email}! This is a test notification.",
        data={'test': True, 'timestamp': timezone.now().isoformat()}
    )
    if notification:
        notifications_sent += len(notification)
        print(f"✅ Sent to {user.email}")

print(f"\n✅ Total notifications sent: {notifications_sent}")
```

---

## 📋 **API Endpoint Details**

### **Endpoint:**
```
POST /api/notifications/send/
```

### **Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

### **Request Body:**
```json
{
  "notification_type": "system_message",
  "title": "Your notification title",
  "body": "Your notification message",
  "all_users": true,  // Send to all users
  "data": {
    "custom": "data"
  }
}
```

### **Response (Success):**
```json
{
  "message": "Successfully sent 5 notifications",
  "notifications_sent": 5
}
```

### **Response (Error):**
```json
{
  "error": "Failed to send notifications"
}
```

---

## ⚠️ **Important Notes**

1. **Admin Access Required:**
   - You must be logged in as an admin user
   - Regular users cannot send notifications to all users

2. **Device Tokens:**
   - Only users with registered device tokens will receive notifications
   - Users without device tokens will be skipped

3. **Firebase Configuration:**
   - Make sure `firebase-service-account.json` is properly configured
   - Check Firebase console for delivery status

4. **User Preferences:**
   - Users who have disabled push notifications won't receive them
   - Quiet hours are respected

---

## 🧪 **Testing Checklist**

- [ ] Admin token is valid
- [ ] Server is running
- [ ] Users have registered device tokens
- [ ] Firebase credentials are configured
- [ ] Notification sent successfully
- [ ] Check devices for received notifications

---

## 🔍 **Troubleshooting**

### **"Unauthorized" Error:**
- Make sure you're using an admin token
- Token might have expired - login again

### **"Forbidden" Error:**
- Your user doesn't have admin privileges
- Contact system administrator

### **"No notifications sent":**
- Users might not have device tokens registered
- Check `DeviceToken` model in Django admin
- Users might have disabled push notifications

### **Notifications not received:**
- Check Firebase console for delivery status
- Verify device tokens are active
- Check user notification preferences
- Make sure app has notification permissions

---

## 📱 **What Users Will See**

When the notification is sent successfully, users will receive:

**Title:** 🧪 Test Notification - System Check

**Body:** Hello! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅

**Data:**
- `test: true`
- `timestamp: "2025-01-26T12:00:00Z"`
- `message: "Push notification system test"`

---

**Ready to test!** 🚀

