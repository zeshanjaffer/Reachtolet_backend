# Billboard Management API Documentation

This document outlines the API endpoints for managing billboards in the ReachToLet platform.

**Base URL:** `http://44.200.108.209:8000`

---

## 1. List and Create Billboards
**Endpoint:** `/api/billboards/`

### GET: List All Billboards
Retrieves all active and approved billboards. Supports filtering by city, type, and search queries.

**cURL:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/" \
     -H "Accept: application/json"
```

**Expected Response (200 OK):**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "city": "Dubai",
            "description": "Large digital billboard on Sheikh Zayed Road",
            "number_of_boards": 1,
            "average_daily_views": "50000",
            "traffic_direction": "Inbound",
            "road_position": "Left",
            "road_name": "SZR",
            "exposure_time": "10 seconds",
            "price_range": "Monthly",
            "display_height": "5m",
            "display_width": "15m",
            "ooh_media_type": "Digital",
            "images": ["http://44.200.108.209:8000/media/billboards/img1.jpg"],
            "latitude": "25.2048",
            "longitude": "55.2708",
            "views": 120,
            "leads": 5,
            "is_active": true,
            "approval_status": "approved",
            "user_name": "John Doe",
            "is_in_wishlist": false
        }
    ]
}
```

### POST: Create Billboard
Creates a new billboard. **Requires Media Owner role.**

**cURL:**
```bash
curl -X POST "http://44.200.108.209:8000/api/billboards/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your_token>" \
     -d '{
        "city": "Abu Dhabi",
        "description": "Premium spot near Corniche",
        "number_of_boards": 1,
        "average_daily_views": "25000",
        "traffic_direction": "Outbound",
        "road_position": "Right",
        "road_name": "Corniche St",
        "exposure_time": "8 seconds",
        "price_range": "Daily",
        "display_height": "4m",
        "display_width": "10m",
        "advertiser_phone": "+971501234567",
        "company_name": "Media Pro",
        "ooh_media_type": "Static",
        "images": ["http://44.200.108.209:8000/media/billboards/new_img.jpg"],
        "latitude": "24.4539",
        "longitude": "54.3773"
     }'
```

**Expected Response (201 Created):**
```json
{
    "id": 2,
    "city": "Abu Dhabi",
    "approval_status": "pending",
    "message": "Billboard created successfully and is pending approval."
}
```

---

## 2. My Billboards
**Endpoint:** `/api/billboards/my-billboards/`

### GET: List My Billboards
Retrieves all billboards owned by the authenticated user. **Requires Media Owner role.**

**cURL:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/my-billboards/" \
     -H "Authorization: Bearer <your_token>"
```

**Expected Response (200 OK):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "city": "Dubai",
            "approval_status": "approved",
            "is_active": true
        }
    ]
}
```

---

## 3. Billboard Detail
**Endpoint:** `/api/billboards/<id>/`

### GET: Retrieve Details
Gets full information for a specific billboard.

**cURL:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/1/"
```

### PATCH: Update Billboard
Updates specific fields of an existing billboard. **Requires Billboard Ownership.**

**cURL:**
```bash
curl -X PATCH "http://44.200.108.209:8000/api/billboards/1/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your_token>" \
     -d '{
        "description": "Updated description for better reach"
     }'
```

---

## 4. Image Upload
**Endpoint:** `/api/billboards/upload-image/`

### POST: Upload Image
Uploads a billboard image file and returns a publicly accessible URL. **Requires Media Owner role.**

**cURL:**
```bash
curl -X POST "http://44.200.108.209:8000/api/billboards/upload-image/" \
     -H "Authorization: Bearer <your_token>" \
     -F "image=@/path/to/your/image.jpg"
```

**Expected Response (201 Created):**
```json
{
    "url": "http://44.200.108.209:8000/media/billboards/unique_filename.jpg"
}
```

---

## 5. Track/Increment View
**Endpoint:** `/api/billboards/<id>/track-view/` or `/api/billboards/<id>/increment-view/`

### POST: Track View
Increments the view count of a billboard. Prevents owner views and duplicate views from the same IP/User.

**cURL:**
```bash
curl -X POST "http://44.200.108.209:8000/api/billboards/1/track-view/" \
     -H "Accept: application/json"
```

**Expected Response (200 OK):**
```json
{
    "message": "View tracked successfully",
    "billboard_id": 1,
    "current_views": 121,
    "duplicate": false
}
```

---

## 6. Toggle Active Status
**Endpoint:** `/api/billboards/<id>/toggle-active/`

### PATCH: Toggle Status
Toggles the `is_active` status between active and inactive. **Requires Billboard Ownership.**

**cURL:**
```bash
curl -X PATCH "http://44.200.108.209:8000/api/billboards/1/toggle-active/" \
     -H "Authorization: Bearer <your_token>"
```

**Expected Response (200 OK):**
```json
{
    "id": "1",
    "is_active": false,
    "message": "Billboard marked as inactive"
}
```

---

## 7. User Authentication & Session
Endpoints for managing user sessions and tokens.

### POST: Logout
Signals the server to end the session. Client should clear local tokens after receiving success.
**Endpoint:** `/api/users/logout/`

**cURL:**
```bash
curl -X POST "http://44.200.108.209:8000/api/users/logout/" \
     -H "Authorization: Bearer <your_access_token>"
```

**Expected Response (200 OK):**
```json
{
    "message": "Logged out successfully."
}
```

### GET: Validate Token
Checks if the current access token is valid and returns basic user info.
**Endpoint:** `/api/users/validate-token/`

**cURL:**
```bash
curl -X GET "http://44.200.108.209:8000/api/users/validate-token/" \
     -H "Authorization: Bearer <your_access_token>"
```

**Expected Response (200 OK):**
```json
{
    "valid": true,
    "user": {
        "id": 48,
        "email": "zeej@gmail.com",
        "user_type": "advertiser"
    }
}
```

### POST: Refresh Token
Exchange a refresh token for a brand new access and refresh token pair.
**Endpoint:** `/api/users/token/refresh/`

**cURL:**
```bash
curl -X POST "http://44.200.108.209:8000/api/users/token/refresh/" \
     -H "Content-Type: application/json" \
     -d '{
        "refresh": "<your_refresh_token>"
     }'
```

---

## 8. Admin Approval Workflow
Endpoints for administrators to manage billboard listings.

### GET: List Pending Billboards
Retrieves all billboards currently in 'pending' status. **Requires Admin privileges.**
**Endpoint:** `/api/billboards/pending/`

**cURL:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/pending/" \
     -H "Authorization: Bearer <admin_token>"
```

### POST: Update Approval Status
Approve or reject a specific billboard. **Requires Admin privileges.**
**Endpoint:** `/api/billboards/<id>/approval-status/`

**cURL (Approve):**
```bash
curl -X POST "http://44.200.108.209:8000/api/billboards/1/approval-status/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <admin_token>" \
     -d '{
        "action": "approve"
     }'
```

---

### Implementation Notes:
1.  **Authentication:** All protected endpoints require a `Bearer` token in the `Authorization` header.
2.  **Role Restriction:** Write operations are restricted based on user type (`media_owner` for creation, `admin` for approval).
3.  **Token Rotation:** Refreshing a token invalidates the old refresh token and provides a new one.
4.  **Logout:** Simple post-auth endpoint to signal session end.

