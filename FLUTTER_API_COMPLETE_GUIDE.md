# 📱 Flutter App API Complete Guide

Complete API documentation with all endpoints, request/response formats, and expected responses for Flutter implementation.

**Base URL**: `http://localhost:8000/api` (Development)  
**Base URL**: `https://your-domain.com/api` (Production)

---

## 🔐 Authentication Endpoints

### 1. Register User
**Endpoint**: `POST /api/users/register/`  
**Authentication**: Not required  
**Description**: Register a new user account and automatically log in

#### Request Body:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "country_code": "US",
  "user_type": "advertiser"
}
```

#### Required Fields:
- `email` (string, required)
- `password` (string, required, min 8 chars)
- `user_type` (string, required) - `"advertiser"` or `"media_owner"`

#### Optional Fields:
- `name` (string)
- `first_name` (string)
- `last_name` (string)
- `phone` (string, format: `+1234567890`)
- `country_code` (string, 2 uppercase letters, e.g., `"US"`, `"GB"`)

#### Success Response (201 Created):
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user@example.com",
    "user_type": "advertiser"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "User registered successfully"
}
```

#### Error Response (400 Bad Request):
```json
{
  "email": ["This field is required."],
  "password": ["This password is too short."],
  "user_type": ["This field is required."]
}
```

---

### 2. Login
**Endpoint**: `POST /api/users/login/`  
**Authentication**: Not required  
**Description**: Login with email and password to get JWT tokens

#### Request Body:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Success Response (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Error Response (401 Unauthorized):
```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### 3. Validate Token
**Endpoint**: `GET /api/users/validate-token/`  
**Authentication**: Required (Bearer Token)  
**Description**: Check if access token is still valid

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "valid": true,
  "user_id": 1,
  "email": "user@example.com"
}
```

#### Error Response (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 4. Refresh Token
**Endpoint**: `POST /api/users/token/refresh/`  
**Authentication**: Not required  
**Description**: Get new access token using refresh token

#### Request Body:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Success Response (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Error Response (401 Unauthorized):
```json
{
  "detail": "Token is invalid or expired"
}
```

---

### 5. Google Login
**Endpoint**: `POST /api/users/google-login/`  
**Authentication**: Not required  
**Description**: Login/Register using Google OAuth

#### Request Body:
```json
{
  "id_token": "google_id_token_here",
  "user_type": "advertiser"
}
```

#### Required Fields:
- `id_token` (string, required) - Google ID token
- `user_type` (string, optional, default: `"advertiser"`) - `"advertiser"` or `"media_owner"`

#### Success Response (200 OK):
```json
{
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "username": "user@gmail.com",
    "user_type": "advertiser"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Error Response (400 Bad Request):
```json
{
  "detail": "No ID token provided."
}
```

---

## 👤 User Profile Endpoints

### 6. Get User Profile
**Endpoint**: `GET /api/users/profile/`  
**Authentication**: Required (Bearer Token)  
**Description**: Get current user's profile information

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "phone": "+1234567890",
  "country_code": "US",
  "formatted_phone": "US +1234567890",
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "profile_image": "http://localhost:8000/media/profile_images/abc123.jpg",
  "user_type": "advertiser"
}
```

---

### 7. Update User Profile
**Endpoint**: `PUT /api/users/profile/`  
**Authentication**: Required (Bearer Token)  
**Description**: Update current user's profile

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "name": "John Doe Updated",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "country_code": "US"
}
```

#### Note: Cannot update:
- `id`
- `username`
- `email`
- `user_type`

#### Success Response (200 OK):
```json
{
  "id": 1,
  "username": "user@example.com",
  "email": "user@example.com",
  "phone": "+1234567890",
  "country_code": "US",
  "formatted_phone": "US +1234567890",
  "name": "John Doe Updated",
  "first_name": "John",
  "last_name": "Doe",
  "profile_image": "http://localhost:8000/media/profile_images/abc123.jpg",
  "user_type": "advertiser"
}
```

---

### 8. Upload Profile Image
**Endpoint**: `POST /api/users/upload-profile-image/`  
**Authentication**: Required (Bearer Token)  
**Description**: Upload profile image for current user

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### Request Body (Form Data):
```
image: <file>
```

#### Success Response (201 Created):
```json
{
  "url": "http://localhost:8000/media/profile_images/abc123.jpg"
}
```

#### Error Response (400 Bad Request):
```json
{
  "detail": "No image provided."
}
```

---

## 📋 Billboard Endpoints

### 9. Get All Billboards (Public)
**Endpoint**: `GET /api/billboards/`  
**Authentication**: Not required  
**Description**: Get list of approved and active billboards (for map/list view)

#### Query Parameters:
- `page` (integer, optional) - Page number (default: 1)
- `page_size` (integer, optional) - Items per page (default: 20, max: 100)
- `search` (string, optional) - Search in city, description, company_name, road_name
- `ooh_media_type` (string, optional) - Filter by media type
- `city` (string, optional) - Filter by city
- `type` (string, optional) - Filter by type
- `ordering` (string, optional) - Order by field (e.g., `-created_at`, `price_range`, `views`)
- `lat` (float, optional) - Latitude for radius search
- `lng` (float, optional) - Longitude for radius search
- `radius` (float, optional) - Radius in km (requires lat & lng)
- `ne_lat` (float, optional) - Northeast latitude for map bounds
- `ne_lng` (float, optional) - Northeast longitude for map bounds
- `sw_lat` (float, optional) - Southwest latitude for map bounds
- `sw_lng` (float, optional) - Southwest longitude for map bounds
- `cluster` (boolean, optional) - Enable clustering (default: false)
- `zoom` (float, optional) - Zoom level for clustering (default: 10.0)

#### Success Response (200 OK) - Paginated:
```json
{
  "links": {
    "next": "http://localhost:8000/api/billboards/?page=2",
    "previous": null
  },
  "count": 150,
  "total_pages": 8,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      "description": "Premium digital billboard",
      "number_of_boards": "2",
      "average_daily_views": "50000",
      "traffic_direction": "North-South",
      "road_position": "Right side",
      "road_name": "Main Boulevard",
      "exposure_time": "24/7",
      "price_range": "50000-100000",
      "display_height": "10",
      "display_width": "20",
      "advertiser_phone": "+92-300-1234567",
      "advertiser_whatsapp": "+92-300-1234567",
      "company_name": "ABC Media",
      "company_website": "https://www.abcmedia.com",
      "ooh_media_type": "Digital Billboard",
      "ooh_media_id": "DB-001",
      "type": "Premium",
      "images": [
        "http://localhost:8000/media/billboards/billboard1.jpg",
        "http://localhost:8000/media/billboards/billboard2.jpg"
      ],
      "unavailable_dates": ["2025-12-25", "2025-12-31"],
      "latitude": 31.4591,
      "longitude": 74.2429,
      "views": 150,
      "leads": 12,
      "is_active": true,
      "address": "Main Boulevard, Lahore",
      "generator_backup": "Yes",
      "created_at": "2025-11-15T10:30:00Z",
      "user_name": "John Doe",
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "approved_at": "2025-11-16T08:00:00Z",
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": "admin@example.com",
      "rejected_by_username": null,
      "is_in_wishlist": false
    }
  ]
}
```

#### Success Response (200 OK) - Map Bounds (No Pagination):
```json
{
  "count": 1500,
  "clustering_enabled": false,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      ...
    }
  ]
}
```

#### Success Response (200 OK) - With Clustering:
```json
{
  "count": 1500,
  "clustered_count": 45,
  "clustering_enabled": true,
  "zoom_level": 10.5,
  "clusters": [
    {
      "type": "cluster",
      "latitude": 31.4591,
      "longitude": 74.2429,
      "count": 25,
      "billboards": []
    },
    {
      "type": "marker",
      "latitude": 31.4600,
      "longitude": 74.2430,
      "billboard": {
        "id": 1,
        "city": "Lahore",
        ...
      }
    }
  ]
}
```

---

### 10. Create Billboard
**Endpoint**: `POST /api/billboards/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner only  
**Description**: Create a new billboard (status: pending)

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "city": "Lahore",
  "description": "Premium digital billboard location",
  "number_of_boards": "2",
  "average_daily_views": "50000",
  "traffic_direction": "North-South",
  "road_position": "Right side",
  "road_name": "Main Boulevard",
  "exposure_time": "24/7",
  "price_range": "50000-100000",
  "display_height": "10",
  "display_width": "20",
  "advertiser_phone": "+92-300-1234567",
  "advertiser_whatsapp": "+92-300-1234567",
  "company_name": "ABC Media",
  "company_website": "https://www.abcmedia.com",
  "ooh_media_type": "Digital Billboard",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [
    "http://localhost:8000/media/billboards/billboard1.jpg"
  ],
  "unavailable_dates": ["2025-12-25", "2025-12-31"],
  "latitude": 31.4591,
  "longitude": 74.2429,
  "address": "Main Boulevard, Lahore",
  "generator_backup": "Yes"
}
```

#### Success Response (201 Created):
```json
{
  "id": 1,
  "city": "Lahore",
  "description": "Premium digital billboard location",
  ...
  "approval_status": "pending",
  "created_at": "2025-11-15T10:30:00Z"
}
```

#### Error Response (403 Forbidden):
```json
{
  "detail": "Only media owners can create billboards. You are registered as an advertiser."
}
```

---

### 11. Get Billboard Detail
**Endpoint**: `GET /api/billboards/{id}/`  
**Authentication**: Not required  
**Description**: Get detailed information about a specific billboard

#### Success Response (200 OK):
```json
{
  "id": 1,
  "city": "Lahore",
  "description": "Premium digital billboard",
  ...
  "is_in_wishlist": false
}
```

#### Error Response (404 Not Found):
```json
{
  "detail": "Not found."
}
```

---

### 12. Update Billboard
**Endpoint**: `PUT /api/billboards/{id}/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner (own billboards only)  
**Description**: Update a billboard

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body: (Same as Create, all fields optional)

#### Success Response (200 OK):
```json
{
  "id": 1,
  "city": "Lahore Updated",
  ...
}
```

#### Error Response (403 Forbidden):
```json
{
  "detail": "You can only update your own billboards."
}
```

---

### 13. Delete Billboard
**Endpoint**: `DELETE /api/billboards/{id}/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner (own billboards only)  
**Description**: Delete a billboard

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (204 No Content):
(No response body)

#### Error Response (403 Forbidden):
```json
{
  "detail": "You can only delete your own billboards."
}
```

---

### 14. Get My Billboards
**Endpoint**: `GET /api/billboards/my-billboards/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner only  
**Description**: Get all billboards created by current user (all statuses: pending, approved, rejected)

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Query Parameters:
- `page` (integer, optional)
- `page_size` (integer, optional)
- `search` (string, optional)
- `city` (string, optional)
- `ooh_media_type` (string, optional)
- `type` (string, optional)
- `is_active` (boolean, optional)
- `approval_status` (string, optional) - `"pending"`, `"approved"`, `"rejected"`
- `ordering` (string, optional)

#### Success Response (200 OK):
```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 5,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      ...
      "approval_status": "pending",
      "approval_status_display": "Pending",
      "approved_at": null,
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": null,
      "rejected_by_username": null,
      "is_in_wishlist": false
    }
  ]
}
```

#### Error Response (403 Forbidden):
```json
{
  "detail": "Only media owners can access their billboards. You are registered as an advertiser."
}
```

---

### 15. Toggle Billboard Active/Inactive
**Endpoint**: `PATCH /api/billboards/{billboard_id}/toggle-active/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner (own billboards only)  
**Description**: Toggle billboard active status

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "id": "1",
  "is_active": false,
  "message": "Billboard marked as inactive"
}
```

#### Error Response (403 Forbidden):
```json
{
  "error": "You can only toggle your own billboards"
}
```

---

### 16. Upload Billboard Image
**Endpoint**: `POST /api/billboards/upload-image/`  
**Authentication**: Required (Bearer Token)  
**Permission**: Media Owner only  
**Description**: Upload billboard image

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### Request Body (Form Data):
```
image: <file>
```

#### Success Response (201 Created):
```json
{
  "url": "http://localhost:8000/media/billboards/abc123.jpg"
}
```

---

### 17. Track Billboard View
**Endpoint**: `POST /api/billboards/{billboard_id}/track-view/`  
**Authentication**: Not required (but recommended)  
**Description**: Track a view for a billboard (prevents duplicate views)

#### Headers (Optional):
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "message": "View tracked successfully",
  "billboard_id": 1,
  "current_views": 151,
  "owner_view": false,
  "duplicate": false
}
```

#### Response (Owner View - Not Tracked):
```json
{
  "message": "View not tracked - owner viewing own billboard",
  "billboard_id": 1,
  "current_views": 150,
  "owner_view": true
}
```

---

### 18. Track Billboard Lead
**Endpoint**: `POST /api/billboards/{billboard_id}/track-lead/`  
**Authentication**: Not required (but recommended)  
**Description**: Track a lead (phone/WhatsApp click) for a billboard

#### Headers (Optional):
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "message": "Lead tracked successfully",
  "billboard_id": 1,
  "current_leads": 13,
  "duplicate": false
}
```

#### Response (Owner Lead - Not Tracked):
```json
{
  "message": "Lead not tracked - owner viewing own billboard",
  "billboard_id": 1,
  "current_leads": 12,
  "owner_lead": true
}
```

---

## ❤️ Wishlist Endpoints

### 19. Get Wishlist
**Endpoint**: `GET /api/billboards/wishlist/`  
**Authentication**: Required (Bearer Token)  
**Description**: Get user's wishlist

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Query Parameters:
- `page` (integer, optional)
- `page_size` (integer, optional)
- `search` (string, optional)
- `ordering` (string, optional)

#### Success Response (200 OK):
```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 3,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "billboard": {
        "id": 5,
        "city": "Lahore",
        ...
      },
      "created_at": "2025-11-15T10:30:00Z"
    }
  ]
}
```

---

### 20. Add to Wishlist
**Endpoint**: `POST /api/billboards/wishlist/`  
**Authentication**: Required (Bearer Token)  
**Description**: Add a billboard to wishlist

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "billboard_id": 1
}
```

#### Success Response (201 Created):
```json
{
  "id": 1,
  "billboard": {
    "id": 1,
    "city": "Lahore",
    ...
  },
  "created_at": "2025-11-15T10:30:00Z"
}
```

#### Error Response (400 Bad Request):
```json
{
  "message": "Billboard is already in your wishlist"
}
```

---

### 21. Remove from Wishlist
**Endpoint**: `DELETE /api/billboards/wishlist/{billboard_id}/remove/`  
**Authentication**: Required (Bearer Token)  
**Description**: Remove a billboard from wishlist

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "message": "Removed from wishlist successfully"
}
```

#### Error Response (404 Not Found):
```json
{
  "message": "Item not found in wishlist"
}
```

---

### 22. Toggle Wishlist
**Endpoint**: `POST /api/billboards/wishlist/{billboard_id}/toggle/`  
**Authentication**: Required (Bearer Token)  
**Description**: Toggle wishlist status (add if not in wishlist, remove if in wishlist)

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK) - Removed:
```json
{
  "message": "Removed from wishlist",
  "in_wishlist": false
}
```

#### Success Response (201 Created) - Added:
```json
{
  "message": "Added to wishlist",
  "in_wishlist": true
}
```

---

## 🔔 Notification Endpoints

### 23. Register Device Token
**Endpoint**: `POST /api/notifications/device-token/register/`  
**Authentication**: Required (Bearer Token)  
**Description**: Register device token for push notifications

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "fcm_token": "device_fcm_token_here",
  "device_type": "android",
  "device_id": "unique_device_id",
  "app_version": "1.0.0",
  "os_version": "Android 13"
}
```

#### Required Fields:
- `fcm_token` (string, required)

#### Optional Fields:
- `device_type` (string, default: `"android"`) - `"android"` or `"ios"`
- `device_id` (string)
- `app_version` (string)
- `os_version` (string)

#### Success Response (201 Created):
```json
{
  "message": "Device token registered successfully",
  "device_token": {
    "id": 1,
    "fcm_token": "device_fcm_token_here",
    "device_type": "android",
    "is_active": true,
    "created_at": "2025-11-15T10:30:00Z"
  }
}
```

---

### 24. Unregister Device Token
**Endpoint**: `POST /api/notifications/device-token/unregister/`  
**Authentication**: Required (Bearer Token)  
**Description**: Unregister device token

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "fcm_token": "device_fcm_token_here"
}
```

#### Success Response (200 OK):
```json
{
  "message": "Device token unregistered successfully"
}
```

---

### 25. Get Notification Preferences
**Endpoint**: `GET /api/notifications/preferences/`  
**Authentication**: Required (Bearer Token)  
**Description**: Get user's notification preferences

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "id": 1,
  "billboard_updates": true,
  "new_billboards": true,
  "promotions": false,
  "marketing": false
}
```

---

### 26. Update Notification Preferences
**Endpoint**: `PUT /api/notifications/preferences/`  
**Authentication**: Required (Bearer Token)  
**Description**: Update notification preferences

#### Headers:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Request Body:
```json
{
  "billboard_updates": true,
  "new_billboards": true,
  "promotions": false,
  "marketing": false
}
```

#### Success Response (200 OK):
```json
{
  "id": 1,
  "billboard_updates": true,
  "new_billboards": true,
  "promotions": false,
  "marketing": false
}
```

---

### 27. Get User Notifications
**Endpoint**: `GET /api/notifications/notifications/`  
**Authentication**: Required (Bearer Token)  
**Description**: Get user's notifications

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Query Parameters:
- `page` (integer, optional)
- `page_size` (integer, optional)
- `limit` (integer, optional)
- `offset` (integer, optional)

#### Success Response (200 OK):
```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 10,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": "uuid-here",
      "notification_type": "billboard_approved",
      "notification_type_display": "Billboard Approved",
      "title": "Your billboard has been approved",
      "body": "Your billboard in Lahore has been approved by admin",
      "device_type": "android",
      "device_type_display": "Android",
      "data": {
        "billboard_id": 1
      },
      "sent_at": "2025-11-15T10:30:00Z",
      "delivered": true,
      "delivered_at": "2025-11-15T10:30:01Z",
      "opened": false,
      "opened_at": null,
      "error_message": null
    }
  ]
}
```

---

### 28. Mark Notification as Opened
**Endpoint**: `POST /api/notifications/notifications/{notification_id}/mark-opened/`  
**Authentication**: Required (Bearer Token)  
**Description**: Mark a notification as opened

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "message": "Notification marked as opened",
  "notification_id": "uuid-here"
}
```

---

### 29. Mark All Notifications as Opened
**Endpoint**: `POST /api/notifications/notifications/mark-all-opened/`  
**Authentication**: Required (Bearer Token)  
**Description**: Mark all user's notifications as opened

#### Headers:
```
Authorization: Bearer <access_token>
```

#### Success Response (200 OK):
```json
{
  "message": "All notifications marked as opened",
  "count": 5
}
```

---

## 🌍 Utility Endpoints

### 30. Get Country Codes
**Endpoint**: `GET /api/users/country-codes/`  
**Authentication**: Not required  
**Description**: Get list of available country codes

#### Success Response (200 OK):
```json
{
  "countries": [
    {
      "code": "US",
      "name": "United States",
      "dial_code": "+1"
    },
    {
      "code": "GB",
      "name": "United Kingdom",
      "dial_code": "+44"
    }
  ],
  "total": 119
}
```

---

### 31. Health Check
**Endpoint**: `GET /api/users/health/`  
**Authentication**: Not required  
**Description**: Check if backend is running

#### Success Response (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T10:30:00Z",
  "message": "Users backend is running"
}
```

---

## 📊 Common Response Patterns

### Pagination Response:
```json
{
  "links": {
    "next": "http://localhost:8000/api/billboards/?page=2",
    "previous": null
  },
  "count": 150,
  "total_pages": 8,
  "current_page": 1,
  "results": [...]
}
```

### Error Response (400 Bad Request):
```json
{
  "field_name": ["Error message here"],
  "another_field": ["Another error message"]
}
```

### Error Response (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Error Response (403 Forbidden):
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Error Response (404 Not Found):
```json
{
  "detail": "Not found."
}
```

### Error Response (500 Internal Server Error):
```json
{
  "error": "Internal server error message"
}
```

---

## 🔑 Authentication Flow

### Standard Flow:
1. **App Startup**: Check for stored tokens
2. **Validate Token**: `GET /api/users/validate-token/` with stored access token
3. **If 200**: User is logged in, proceed to main app
4. **If 401**: Token expired, try refresh with `POST /api/users/token/refresh/`
5. **If refresh fails**: Redirect to login/onboarding screen

### Token Storage:
- Store both `access` and `refresh` tokens securely
- Access token expires in 1 day
- Refresh token expires in 7 days
- Always include access token in `Authorization: Bearer <token>` header

---

## 📝 Notes for Flutter Implementation

1. **Base URL**: Use environment variables for base URL (dev/prod)
2. **Token Storage**: Use `flutter_secure_storage` or `shared_preferences` for tokens
3. **Error Handling**: Always handle 401 (unauthorized) and 403 (forbidden) responses
4. **Pagination**: Implement infinite scroll or load more for paginated endpoints
5. **Image Upload**: Use `multipart/form-data` for image uploads
6. **Network Timeout**: Set appropriate timeout (e.g., 30 seconds)
7. **Retry Logic**: Implement retry for failed requests (especially token refresh)
8. **Offline Support**: Cache responses where appropriate

---

## 🎯 Quick Reference

| Endpoint | Method | Auth | Permission |
|----------|--------|------|------------|
| Register | POST | ❌ | Public |
| Login | POST | ❌ | Public |
| Validate Token | GET | ✅ | Any |
| Refresh Token | POST | ❌ | Public |
| Google Login | POST | ❌ | Public |
| Get Profile | GET | ✅ | Any |
| Update Profile | PUT | ✅ | Any |
| Upload Profile Image | POST | ✅ | Any |
| Get Billboards | GET | ❌ | Public |
| Create Billboard | POST | ✅ | Media Owner |
| Get Billboard Detail | GET | ❌ | Public |
| Update Billboard | PUT | ✅ | Media Owner (Own) |
| Delete Billboard | DELETE | ✅ | Media Owner (Own) |
| My Billboards | GET | ✅ | Media Owner |
| Toggle Active | PATCH | ✅ | Media Owner (Own) |
| Track View | POST | ❌ | Public |
| Track Lead | POST | ❌ | Public |
| Get Wishlist | GET | ✅ | Any |
| Add to Wishlist | POST | ✅ | Any |
| Remove from Wishlist | DELETE | ✅ | Any |
| Toggle Wishlist | POST | ✅ | Any |
| Register Device Token | POST | ✅ | Any |
| Unregister Device Token | POST | ✅ | Any |
| Get Notifications | GET | ✅ | Any |
| Mark Notification Opened | POST | ✅ | Any |
| Get Country Codes | GET | ❌ | Public |
| Health Check | GET | ❌ | Public |

---

**Last Updated**: 2025-01-26  
**API Version**: v1

