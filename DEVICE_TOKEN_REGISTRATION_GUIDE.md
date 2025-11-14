# How Device Tokens Are Saved - Complete Guide

## 🔄 **Complete Flow: From Mobile App to Database**

### **Step-by-Step Process:**

```
1. User Opens App
   ↓
2. App Gets FCM Token from Firebase
   ↓
3. App Calls Backend API with Token
   ↓
4. Backend Validates & Saves Token
   ↓
5. Token Stored in Database
   ↓
6. Ready to Receive Notifications!
```

---

## 📱 **1. Mobile App Side (What Your App Needs to Do)**

### **When User Logs In:**

The mobile app should automatically:

1. **Initialize Firebase Messaging**
2. **Request Notification Permissions**
3. **Get FCM Token**
4. **Register Token with Backend**

### **Example Code (Flutter):**

```dart
// When user logs in successfully
Future<void> registerDeviceToken() async {
  // 1. Get FCM token
  String? fcmToken = await FirebaseMessaging.instance.getToken();
  
  if (fcmToken != null) {
    // 2. Send to backend
    final response = await http.post(
      Uri.parse('http://44.200.108.209:8000/api/notifications/device-token/register/'),
      headers: {
        'Authorization': 'Bearer ${userToken}', // User's auth token
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'fcm_token': fcmToken,
        'device_type': Platform.isIOS ? 'ios' : 'android',
        'device_id': await getDeviceId(), // Optional
        'app_version': '1.0.0', // Optional
        'os_version': 'Android 13', // Optional
      }),
    );
    
    if (response.statusCode == 201) {
      print('✅ Token registered successfully!');
    }
  }
}
```

### **Example Code (React Native):**

```javascript
import messaging from '@react-native-firebase/messaging';

// When user logs in
async function registerDeviceToken(userToken) {
  try {
    // 1. Request permission
    const authStatus = await messaging().requestPermission();
    
    if (authStatus === messaging.AuthorizationStatus.AUTHORIZED) {
      // 2. Get FCM token
      const fcmToken = await messaging().getToken();
      
      // 3. Send to backend
      const response = await fetch(
        'http://44.200.108.209:8000/api/notifications/device-token/register/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            fcm_token: fcmToken,
            device_type: Platform.OS, // 'ios' or 'android'
            device_id: DeviceInfo.getUniqueId(),
            app_version: DeviceInfo.getVersion(),
            os_version: DeviceInfo.getSystemVersion(),
          }),
        }
      );
      
      if (response.ok) {
        console.log('✅ Token registered successfully!');
      }
    }
  } catch (error) {
    console.error('Failed to register token:', error);
  }
}
```

---

## 🔌 **2. Backend API Endpoint**

### **Endpoint:**
```
POST /api/notifications/device-token/register/
```

### **Required Headers:**
```
Authorization: Bearer <user_auth_token>
Content-Type: application/json
```

### **Request Body:**
```json
{
  "fcm_token": "dK3jF8h2...",  // Required: FCM token from Firebase
  "device_type": "android",    // Required: "ios", "android", or "web"
  "device_id": "device123",     // Optional: Unique device identifier
  "app_version": "1.0.0",        // Optional: App version
  "os_version": "Android 13"     // Optional: OS version
}
```

### **Success Response (201):**
```json
{
  "message": "Device token registered successfully",
  "device_token": {
    "id": 1,
    "fcm_token": "dK3jF8h2...",
    "device_type": "android",
    "is_active": true,
    "created_at": "2025-01-26T12:00:00Z"
  }
}
```

---

## 💾 **3. Backend Processing (What Happens)**

### **Step 1: API View Receives Request**
```python
# notifications/views.py
class DeviceTokenView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        # Validates the request
        # Extracts user from auth token
        # Calls push_service.register_device_token()
```

### **Step 2: Service Registers Token**
```python
# notifications/services.py
def register_device_token(self, user, fcm_token, device_type='android', ...):
    # Uses update_or_create to:
    # - Create new token if it doesn't exist
    # - Update existing token if it already exists (same FCM token)
    
    device_token, created = DeviceToken.objects.update_or_create(
        fcm_token=fcm_token,  # Unique identifier
        defaults={
            'user': user,              # Link to user
            'device_type': device_type,
            'device_id': device_id,
            'app_version': app_version,
            'os_version': os_version,
            'is_active': True          # Mark as active
        }
    )
```

### **Step 3: Token Saved to Database**
The token is saved in the `notifications_device_token` table with:
- **user**: Foreign key to the user
- **fcm_token**: The Firebase token (unique)
- **device_type**: iOS, Android, or Web
- **is_active**: True (can receive notifications)
- **created_at**: Timestamp
- **last_used**: Auto-updated on each use

---

## 🗄️ **4. Database Structure**

### **DeviceToken Model:**
```python
class DeviceToken(models.Model):
    user = ForeignKey(User)           # Which user owns this device
    fcm_token = CharField(unique=True) # Firebase token (unique)
    device_type = CharField()         # 'ios', 'android', 'web'
    device_id = CharField()           # Optional device ID
    app_version = CharField()         # Optional app version
    os_version = CharField()          # Optional OS version
    is_active = BooleanField()        # Can receive notifications?
    created_at = DateTimeField()      # When registered
    last_used = DateTimeField()      # Last time used
```

### **Database Table: `notifications_device_token`**

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to User |
| fcm_token | String (255) | Firebase token (unique) |
| device_type | String (10) | 'ios', 'android', 'web' |
| device_id | String (255) | Optional device identifier |
| app_version | String (20) | Optional app version |
| os_version | String (20) | Optional OS version |
| is_active | Boolean | Active status |
| created_at | DateTime | Registration time |
| last_used | DateTime | Last update time |

---

## 🔄 **5. Token Update Logic**

### **Smart Update Behavior:**

The system uses `update_or_create()` which means:

1. **If token doesn't exist:**
   - Creates new record
   - Links to current user
   - Sets `is_active = True`

2. **If token already exists:**
   - Updates the existing record
   - Updates user (if user changed)
   - Updates device info
   - Sets `is_active = True`
   - Updates `last_used` timestamp

### **Why This is Important:**

- **Same device, different user:** Token gets reassigned to new user
- **User logs in on same device:** Token gets updated, stays active
- **Token refresh:** Firebase may refresh tokens, old token gets updated

---

## 📋 **6. When Tokens Are Registered**

### **Automatic Registration (Recommended):**

The app should register tokens:

1. **On App Launch** (if user is logged in)
2. **After User Login** (immediately after successful login)
3. **On Token Refresh** (Firebase may refresh tokens)
4. **On App Update** (to update app_version)

### **Token Refresh Handling:**

```dart
// Listen for token refresh
FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
  registerDeviceToken(newToken); // Re-register automatically
});
```

---

## ✅ **7. Verification**

### **Check in Django Admin:**

1. Go to: `http://44.200.108.209:8000/admin/notifications/devicetoken/`
2. You should see registered tokens
3. Each token shows:
   - User email
   - Device type
   - FCM token (truncated)
   - Active status
   - Created date

### **Check via API:**

```bash
# Get your device tokens (as logged-in user)
GET http://44.200.108.209:8000/api/notifications/device-token/register/
Authorization: Bearer <your_token>
```

---

## 🚨 **8. Common Issues & Solutions**

### **Issue 1: Token Not Saving**

**Problem:** API returns error  
**Solution:**
- Check authentication token is valid
- Verify FCM token format
- Check server logs for errors

### **Issue 2: Token Saved But Not Receiving Notifications**

**Problem:** Token exists but notifications not delivered  
**Solution:**
- Check `is_active = True` in database
- Verify Firebase credentials are correct
- Check user notification preferences
- Verify token is still valid (Firebase may invalidate old tokens)

### **Issue 3: Multiple Tokens for Same User**

**Problem:** User has multiple devices  
**Solution:** This is normal! Each device gets its own token. Notifications are sent to all active tokens.

### **Issue 4: Token Becomes Inactive**

**Problem:** Token marked as `is_active = False`  
**Solution:**
- Happens when Firebase says token is invalid
- User needs to re-register token
- App should handle token refresh automatically

---

## 🔍 **9. Testing Token Registration**

### **Manual Test with cURL:**

```bash
curl -X POST http://44.200.108.209:8000/api/notifications/device-token/register/ \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "test_token_12345",
    "device_type": "android",
    "device_id": "test_device_123",
    "app_version": "1.0.0",
    "os_version": "Android 13"
  }'
```

### **Expected Response:**
```json
{
  "message": "Device token registered successfully",
  "device_token": {
    "fcm_token": "test_token_12345",
    "device_type": "android",
    "is_active": true
  }
}
```

---

## 📊 **10. Summary**

### **Complete Flow:**

1. ✅ **User logs in** → App gets auth token
2. ✅ **App requests FCM token** → Firebase provides token
3. ✅ **App calls backend API** → `POST /api/notifications/device-token/register/`
4. ✅ **Backend validates** → Checks auth token, validates data
5. ✅ **Backend saves token** → Creates/updates DeviceToken record
6. ✅ **Token stored in DB** → Ready for notifications!

### **Key Points:**

- ✅ Tokens are **automatically saved** when app calls the API
- ✅ Each user can have **multiple tokens** (multiple devices)
- ✅ Tokens are **updated automatically** if they already exist
- ✅ Invalid tokens are **automatically deactivated**
- ✅ System handles **token refresh** automatically

---

## 🎯 **Next Steps for Your App**

1. **Implement token registration** in your mobile app
2. **Call the API** after user login
3. **Handle token refresh** events
4. **Test with real device** to verify tokens are saved
5. **Check admin panel** to see registered tokens

**Once tokens are registered, notifications will work automatically!** 🚀

