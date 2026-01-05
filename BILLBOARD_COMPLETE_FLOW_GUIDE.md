# 🎯 Complete Billboard Management Flow Guide

## 📋 Flow Overview

1. **Media Owner Creates Billboard** → Status: `pending`
2. **Admin Reviews & Approves** → Status: `approved`
3. **Billboard Appears on Map** (if `is_active: true`)
4. **Media Owner Can**: Edit, Delete, Toggle Active/Inactive

---

## 🔄 Complete Flow Diagram

```
Media Owner                    Admin                    Public Map
     │                          │                          │
     ├─ 1. Create Billboard ────┼──────────────────────────┤
     │   (status: pending)      │                          │
     │                          │                          │
     │                          ├─ 2. Approve ─────────────┤
     │                          │   (status: approved)     │
     │                          │                          │
     │                          │                          ├─ 3. Visible on Map
     │                          │                          │   (if is_active: true)
     │                          │                          │
     ├─ 4. Edit Billboard ──────┼──────────────────────────┤
     ├─ 5. Delete Billboard ────┼──────────────────────────┤
     └─ 6. Toggle Active ───────┼──────────────────────────┤
        (show/hide on map)      │                          │
```

---

## 1️⃣ CREATE BILLBOARD (Media Owner Only)

### cURL Command
```bash
curl -X POST "http://localhost:8000/api/billboards/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Lahore",
    "description": "Premium digital billboard located at main highway",
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
    "images": [],
    "unavailable_dates": [],
    "latitude": 31.4591,
    "longitude": 74.2429,
    "address": "Main Boulevard, Lahore",
    "generator_backup": "Yes"
  }'
```

### Expected Response (201 Created)
```json
{
  "id": 1,
  "city": "Lahore",
  "description": "Premium digital billboard located at main highway",
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
  "images": [],
  "unavailable_dates": [],
  "latitude": 31.4591,
  "longitude": 74.2429,
  "views": 0,
  "leads": 0,
  "is_active": true,
  "address": "Main Boulevard, Lahore",
  "generator_backup": "Yes",
  "created_at": "2025-11-22T20:00:00Z",
  "user_name": "John Doe",
  "approval_status": "pending",
  "approval_status_display": "Pending",
  "approved_at": null,
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": null,
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication required to create billboards"
}
```

**403 Forbidden (Advertiser trying to create):**
```json
{
  "detail": "Only media owners can create billboards. You are registered as an advertiser."
}
```

**400 Bad Request (Missing required fields):**
```json
{
  "city": ["This field is required."],
  "ooh_media_type": ["This field is required."],
  "type": ["This field is required."]
}
```

---

## 2️⃣ ADMIN: GET PENDING BILLBOARDS

### cURL Command
```bash
curl -X GET "http://localhost:8000/api/billboards/pending/" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      "description": "Premium digital billboard located at main highway",
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
      "images": [],
      "unavailable_dates": [],
      "latitude": 31.4591,
      "longitude": 74.2429,
      "views": 0,
      "leads": 0,
      "is_active": true,
      "address": "Main Boulevard, Lahore",
      "generator_backup": "Yes",
      "created_at": "2025-11-22T20:00:00Z",
      "user_name": "John Doe",
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

---

## 3️⃣ ADMIN: APPROVE BILLBOARD

### cURL Command
```bash
curl -X POST "http://localhost:8000/api/billboards/1/approval-status/" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve"
  }'
```

### Expected Response (200 OK)
```json
{
  "message": "Billboard approved successfully",
  "billboard": {
    "id": 1,
    "city": "Lahore",
    "description": "Premium digital billboard located at main highway",
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
    "images": [],
    "unavailable_dates": [],
    "latitude": 31.4591,
    "longitude": 74.2429,
    "views": 0,
    "leads": 0,
    "is_active": true,
    "address": "Main Boulevard, Lahore",
    "generator_backup": "Yes",
    "created_at": "2025-11-22T20:00:00Z",
    "user_name": "John Doe",
    "approval_status": "approved",
    "approval_status_display": "Approved",
    "approved_at": "2025-11-22T20:05:00Z",
    "rejected_at": null,
    "rejection_reason": null,
    "approved_by_username": "admin",
    "rejected_by_username": null,
    "is_in_wishlist": false
  }
}
```

### Admin: REJECT BILLBOARD

```bash
curl -X POST "http://localhost:8000/api/billboards/1/approval-status/" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "rejection_reason": "Poor image quality"
  }'
```

**Response (200 OK):**
```json
{
  "message": "Billboard rejected successfully",
  "billboard": {
    "id": 1,
    "approval_status": "rejected",
    "approval_status_display": "Rejected",
    "rejected_at": "2025-11-22T20:05:00Z",
    "rejection_reason": "Poor image quality",
    "rejected_by_username": "admin",
    "approved_at": null,
    "approved_by_username": null
  }
}
```

---

## 4️⃣ PUBLIC: VIEW BILLBOARDS ON MAP (After Approval)

### cURL Command
```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2&cluster=true&zoom=10" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "count": 15,
  "clustered_count": 5,
  "clustering_enabled": true,
  "zoom_level": 10.0,
  "clusters": [
    {
      "type": "cluster",
      "latitude": 31.4591,
      "longitude": 74.2429,
      "count": 3,
      "bounds": {
        "ne_lat": 31.4600,
        "ne_lng": 74.2450,
        "sw_lat": 31.4580,
        "sw_lng": 74.2400
      }
    },
    {
      "type": "marker",
      "id": 1,
      "latitude": 31.4700,
      "longitude": 74.2500,
      "data": {
        "id": 1,
        "city": "Lahore",
        "description": "Premium digital billboard located at main highway",
        "latitude": 31.4700,
        "longitude": 74.2500,
        "company_name": "ABC Media",
        "ooh_media_type": "Digital Billboard",
        "price_range": "50000-100000",
        "images": [],
        "views": 0,
        "leads": 0,
        "is_active": true,
        "address": "Main Boulevard, Lahore",
        "approval_status": "approved"
      }
    }
  ]
}
```

**Note:** Only billboards with `approval_status: "approved"` AND `is_active: true` appear on the map.

---

## 5️⃣ MEDIA OWNER: GET MY BILLBOARDS

### cURL Command
```bash
curl -X GET "http://localhost:8000/api/billboards/my-billboards/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
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
      "city": "Lahore",
      "description": "Premium digital billboard located at main highway",
      "company_name": "ABC Media",
      "ooh_media_type": "Digital Billboard",
      "type": "Premium",
      "latitude": 31.4591,
      "longitude": 74.2429,
      "views": 150,
      "leads": 12,
      "is_active": true,
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "created_at": "2025-11-22T20:00:00Z"
    },
    {
      "id": 2,
      "city": "Karachi",
      "description": "Static billboard",
      "company_name": "XYZ Media",
      "ooh_media_type": "Static Billboard",
      "type": "Standard",
      "latitude": 24.8607,
      "longitude": 67.0011,
      "views": 89,
      "leads": 5,
      "is_active": false,
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "created_at": "2025-11-21T15:00:00Z"
    },
    {
      "id": 3,
      "city": "Islamabad",
      "description": "New billboard",
      "company_name": "New Media",
      "ooh_media_type": "LED Display",
      "type": "Premium",
      "latitude": 33.6844,
      "longitude": 73.0479,
      "views": 0,
      "leads": 0,
      "is_active": true,
      "approval_status": "pending",
      "approval_status_display": "Pending",
      "created_at": "2025-11-22T21:00:00Z"
    }
  ]
}
```

---

## 6️⃣ MEDIA OWNER: GET SINGLE BILLBOARD DETAIL

### cURL Command
```bash
curl -X GET "http://localhost:8000/api/billboards/1/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK)
```json
{
  "id": 1,
  "city": "Lahore",
  "description": "Premium digital billboard located at main highway",
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
  "images": [],
  "unavailable_dates": [],
  "latitude": 31.4591,
  "longitude": 74.2429,
  "views": 150,
  "leads": 12,
  "is_active": true,
  "address": "Main Boulevard, Lahore",
  "generator_backup": "Yes",
  "created_at": "2025-11-22T20:00:00Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2025-11-22T20:05:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": "admin",
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

---

## 7️⃣ MEDIA OWNER: EDIT BILLBOARD

### cURL Command
```bash
curl -X PUT "http://localhost:8000/api/billboards/1/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Lahore",
    "description": "Updated description - Premium digital billboard",
    "number_of_boards": "3",
    "average_daily_views": "60000",
    "traffic_direction": "North-South",
    "road_position": "Right side",
    "road_name": "Main Boulevard",
    "exposure_time": "24/7",
    "price_range": "60000-120000",
    "display_height": "12",
    "display_width": "24",
    "advertiser_phone": "+92-300-1234567",
    "advertiser_whatsapp": "+92-300-1234567",
    "company_name": "ABC Media Updated",
    "company_website": "https://www.abcmedia.com",
    "ooh_media_type": "Digital Billboard",
    "ooh_media_id": "DB-001",
    "type": "Premium",
    "images": [],
    "unavailable_dates": [],
    "latitude": 31.4591,
    "longitude": 74.2429,
    "address": "Main Boulevard, Lahore",
    "generator_backup": "Yes"
  }'
```

### Expected Response (200 OK)
```json
{
  "id": 1,
  "city": "Lahore",
  "description": "Updated description - Premium digital billboard",
  "number_of_boards": "3",
  "average_daily_views": "60000",
  "traffic_direction": "North-South",
  "road_position": "Right side",
  "road_name": "Main Boulevard",
  "exposure_time": "24/7",
  "price_range": "60000-120000",
  "display_height": "12",
  "display_width": "24",
  "advertiser_phone": "+92-300-1234567",
  "advertiser_whatsapp": "+92-300-1234567",
  "company_name": "ABC Media Updated",
  "company_website": "https://www.abcmedia.com",
  "ooh_media_type": "Digital Billboard",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [],
  "unavailable_dates": [],
  "latitude": 31.4591,
  "longitude": 74.2429,
  "views": 150,
  "leads": 12,
  "is_active": true,
  "address": "Main Boulevard, Lahore",
  "generator_backup": "Yes",
  "created_at": "2025-11-22T20:00:00Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2025-11-22T20:05:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": "admin",
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

### Error Responses

**403 Forbidden (Not Owner):**
```json
{
  "detail": "You can only update your own billboards."
}
```

**403 Forbidden (Not Media Owner):**
```json
{
  "detail": "Only media owners can update billboards."
}
```

---

## 8️⃣ MEDIA OWNER: DELETE BILLBOARD

### cURL Command
```bash
curl -X DELETE "http://localhost:8000/api/billboards/1/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response (204 No Content)
```
(Empty response body)
```

### Error Responses

**403 Forbidden (Not Owner):**
```json
{
  "detail": "You can only delete your own billboards."
}
```

**403 Forbidden (Not Media Owner):**
```json
{
  "detail": "Only media owners can delete billboards."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

---

## 9️⃣ MEDIA OWNER: TOGGLE ACTIVE/INACTIVE

### cURL Command
```bash
curl -X PATCH "http://localhost:8000/api/billboards/1/toggle-active/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Expected Response (200 OK - When Toggling to Active)
```json
{
  "id": "1",
  "is_active": true,
  "message": "Billboard marked as active"
}
```

### Expected Response (200 OK - When Toggling to Inactive)
```json
{
  "id": "1",
  "is_active": false,
  "message": "Billboard marked as inactive"
}
```

### Error Responses

**403 Forbidden (Not Owner):**
```json
{
  "error": "You can only toggle your own billboards"
}
```

**403 Forbidden (Not Media Owner):**
```json
{
  "error": "Only media owners can toggle billboard status."
}
```

**404 Not Found:**
```json
{
  "error": "Billboard not found"
}
```

---

## 📊 Complete Status Flow

| Step | Approval Status | Is Active | Visible on Map? |
|------|----------------|-----------|-----------------|
| 1. Created | `pending` | `true` | ❌ No (not approved) |
| 2. Admin Approves | `approved` | `true` | ✅ Yes |
| 3. Owner Deactivates | `approved` | `false` | ❌ No (inactive) |
| 4. Owner Reactivates | `approved` | `true` | ✅ Yes |
| 5. Admin Rejects | `rejected` | `true` | ❌ No (rejected) |

**Rule:** Billboard appears on map ONLY if:
- `approval_status == "approved"` AND
- `is_active == true`

---

## 🔐 Permission Summary

| Action | Who Can Do It | Endpoint |
|--------|---------------|----------|
| Create Billboard | Media Owner | `POST /api/billboards/` |
| View Billboard | Anyone (Public) | `GET /api/billboards/{id}/` |
| View My Billboards | Media Owner (Own Only) | `GET /api/billboards/my-billboards/` |
| Edit Billboard | Media Owner (Own Only) | `PUT /api/billboards/{id}/` |
| Delete Billboard | Media Owner (Own Only) | `DELETE /api/billboards/{id}/` |
| Toggle Active | Media Owner (Own Only) | `PATCH /api/billboards/{id}/toggle-active/` |
| Approve/Reject | Admin Only | `POST /api/billboards/{id}/approval-status/` |
| View Pending | Admin Only | `GET /api/billboards/pending/` |
| View on Map | Public (Approved + Active Only) | `GET /api/billboards/?ne_lat=...` |

---

## 🎯 Flutter Implementation Flow

### Step 1: Media Owner Creates Billboard
```dart
// 1. User fills form and submits
POST /api/billboards/
// Response: approval_status = "pending"
// Show message: "Billboard submitted for approval"
```

### Step 2: Admin Approves (Backend Process)
```
// Admin uses admin panel or API
POST /api/billboards/{id}/approval-status/
// Response: approval_status = "approved"
```

### Step 3: Billboard Appears on Map
```dart
// Public map view automatically shows approved + active billboards
GET /api/billboards/?ne_lat=...&cluster=true
// Response includes billboard in clusters/markers
```

### Step 4: Media Owner Views Their Billboards
```dart
// Show in "My Billboards" screen
GET /api/billboards/my-billboards/
// Shows all billboards (pending, approved, rejected)
```

### Step 5: Media Owner Edits Billboard
```dart
// User edits and saves
PUT /api/billboards/{id}/
// Updates billboard (still approved, visible on map)
```

### Step 6: Media Owner Toggles Active/Inactive
```dart
// User toggles visibility
PATCH /api/billboards/{id}/toggle-active/
// If is_active = false → Removed from map
// If is_active = true → Appears on map (if approved)
```

### Step 7: Media Owner Deletes Billboard
```dart
// User deletes
DELETE /api/billboards/{id}/
// Billboard removed permanently
```

---

## ✅ Complete Test Flow

1. **Create Billboard** → Check `approval_status: "pending"`
2. **Admin Approves** → Check `approval_status: "approved"`
3. **Check Map** → Billboard should appear (if `is_active: true`)
4. **Toggle Inactive** → Billboard disappears from map
5. **Toggle Active** → Billboard reappears on map
6. **Edit Billboard** → Changes saved, still visible
7. **Delete Billboard** → Removed permanently

---

## 📝 Important Notes

1. **Approval Required**: New billboards need admin approval before appearing on map
2. **Active Status**: Even if approved, billboard won't show if `is_active: false`
3. **Owner Only**: Media owners can only edit/delete/toggle their own billboards
4. **Public Map**: Only shows `approved` + `is_active: true` billboards
5. **My Billboards**: Shows all billboards regardless of status (for owner)

---

## 🚀 Quick Reference

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/billboards/` | POST | Media Owner | Create billboard |
| `/api/billboards/{id}/` | GET | Public | View billboard detail |
| `/api/billboards/{id}/` | PUT | Media Owner (Own) | Edit billboard |
| `/api/billboards/{id}/` | DELETE | Media Owner (Own) | Delete billboard |
| `/api/billboards/{id}/toggle-active/` | PATCH | Media Owner (Own) | Toggle active/inactive |
| `/api/billboards/my-billboards/` | GET | Media Owner | Get my billboards |
| `/api/billboards/pending/` | GET | Admin | Get pending billboards |
| `/api/billboards/{id}/approval-status/` | POST | Admin | Approve/reject billboard |
| `/api/billboards/?ne_lat=...` | GET | Public | Get billboards for map |

This complete flow covers all billboard management operations! 🎉

