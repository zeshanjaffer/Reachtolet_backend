# Final API Guide (Postman Ready) — ReachToLet Backend (Flutter)

This file is the **single source of truth** for all **non-admin** APIs in this backend, based on the actual Django `urls.py` and views.

Backend: Django REST Framework + SimpleJWT (JWT Bearer).

---

## Base configuration

### Base URL

- `{{BASE_URL}}` (example: `http://127.0.0.1:8000`)

### Auth header (JWT)

- `Authorization: Bearer {{ACCESS_TOKEN}}`

### Content types

- JSON requests: `Content-Type: application/json`
- Multipart requests: `Content-Type: multipart/form-data`

---

## Platform behavior (roles + visibility)

### User roles

- `advertiser`: browse public billboards, wishlist, track views/leads
- `media_owner`: create/update/delete own billboards, set availability, toggle active/inactive, view “my billboards”

### Public billboard visibility rule

Public endpoints only return billboards where:
- `approval_status = "approved"`
- `is_active = true`

### Availability (calendar) rule

There is **no separate availability endpoint**.

Availability is stored on the billboard record:
- `unavailable_dates`: array of strings in `YYYY-MM-DD` format

To set availability from Flutter:
- create billboard with `unavailable_dates`, or
- update billboard using `PUT /api/billboards/{id}/` or `PATCH /api/billboards/{id}/` with a new `unavailable_dates` array

---

## Common list pagination response

Most list endpoints return:

```json
{
  "links": {
    "next": "http://127.0.0.1:8000/api/billboards/?page=2",
    "previous": null
  },
  "count": 45,
  "total_pages": 3,
  "current_page": 1,
  "results": []
}
```

Query params:
- `page`
- `page_size` (max: 100)

---

## Data objects (reference)

### Billboard (full fields)

This is the full object shape returned by billboard detail/create/update and most billboard lists.

```json
{
  "id": 123,
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [
    "http://127.0.0.1:8000/media/billboards/img1.jpg",
    "http://127.0.0.1:8000/media/billboards/img2.jpg"
  ],
  "unavailable_dates": [
    "2026-04-01",
    "2026-04-02"
  ],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "views": 10,
  "leads": 2,
  "is_active": true,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes",
  "created_at": "2026-03-25T10:30:00Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-03-25T11:00:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": "admin",
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

---

## Users & Authentication (`/api/users/`)

### 1) Register (sign up)

**POST** `/api/users/register/`

**Headers**
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "email": "user@example.com",
  "password": "TestPassword123!",
  "full_name": "John Doe",
  "phone": "+12345678901",
  "country_code": "US",
  "user_type": "advertiser"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/register/' \
--header 'Content-Type: application/json' \
--data-raw '{
  "email": "user@example.com",
  "password": "TestPassword123!",
  "full_name": "John Doe",
  "phone": "+12345678901",
  "country_code": "US",
  "user_type": "advertiser"
}'
```

**Response (201)**

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone": "+12345678901",
    "country_code": "US",
    "user_type": "advertiser"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.refresh_token_example",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.access_token_example",
  "message": "User registered successfully"
}
```

**Response (400)**

```json
{
  "country_code": [
    "Country code must be 2 uppercase letters (e.g., 'US', 'GB')"
  ]
}
```

---

### 2) Login

**POST** `/api/users/login/`

**Headers**
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "email": "user@example.com",
  "password": "TestPassword123!"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/login/' \
--header 'Content-Type: application/json' \
--data-raw '{
  "email": "user@example.com",
  "password": "TestPassword123!"
}'
```

**Response (200)**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.access_token_example",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.refresh_token_example",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "user_type": "advertiser"
  }
}
```

**Response (400)**

```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### 3) Refresh token

**POST** `/api/users/token/refresh/`

**Headers**
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "refresh": "refresh_token_here"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/token/refresh/' \
--header 'Content-Type: application/json' \
--data-raw '{
  "refresh": "refresh_token_here"
}'
```

**Response (200)**

```json
{
  "access": "new_access_token_here"
}
```

**Response (401)**

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 4) Validate token (authenticated)

**GET** `/api/users/validate-token/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/users/validate-token/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "user_type": "advertiser"
  }
}
```

**Response (401)**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 5) Country codes

**GET** `/api/users/country-codes/`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/users/country-codes/'
```

**Response (200)**

```json
{
  "countries": [
    {
      "code": "US",
      "name": "United States",
      "dial_code": "+1"
    }
  ],
  "total": 249
}
```

---

### 6) Get profile (authenticated)

**GET** `/api/users/profile/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/users/profile/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "id": 1,
  "email": "user@example.com",
  "phone": "+12345678901",
  "country_code": "US",
  "formatted_phone": "+12345678901",
  "full_name": "John Doe",
  "profile_image": null,
  "user_type": "advertiser"
}
```

---

### 7) Update profile (authenticated)

**PUT** `/api/users/profile/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "full_name": "John Doe Updated",
  "phone": "+12345678901",
  "country_code": "US",
  "profile_image": null
}
```

**Postman cURL**

```bash
curl --location --request PUT '{{BASE_URL}}/api/users/profile/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "full_name": "John Doe Updated",
  "phone": "+12345678901",
  "country_code": "US",
  "profile_image": null
}'
```

**Response (200)**

```json
{
  "id": 1,
  "email": "user@example.com",
  "phone": "+12345678901",
  "country_code": "US",
  "formatted_phone": "+12345678901",
  "full_name": "John Doe Updated",
  "profile_image": null,
  "user_type": "advertiser"
}
```

---

### 8) Google login

**POST** `/api/users/google-login/`

**Headers**
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "id_token": "google_id_token_here",
  "user_type": "advertiser"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/google-login/' \
--header 'Content-Type: application/json' \
--data-raw '{
  "id_token": "google_id_token_here",
  "user_type": "advertiser"
}'
```

**Response (200)**

```json
{
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "user_type": "advertiser"
  },
  "refresh": "refresh_token_example",
  "access": "access_token_example"
}
```

---

### 9) Upload profile image (authenticated)

**POST** `/api/users/upload-profile-image/` (multipart)

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Body (form-data)**
- `image`: file

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/upload-profile-image/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--form 'image=@"C:\path\to\photo.jpg"'
```

**Response (201)**

```json
{
  "url": "http://127.0.0.1:8000/media/profile_images/profile_123.jpg"
}
```

**Response (400)**

```json
{
  "detail": "No image provided."
}
```

---

### 10) Logout (authenticated)

**POST** `/api/users/logout/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/users/logout/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "message": "Logged out successfully."
}
```

---

### 11) Health

**GET** `/api/users/health/`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/users/health/'
```

**Response (200)**

```json
{
  "status": "healthy",
  "timestamp": "2026-03-25T10:30:00Z",
  "message": "Users backend is running"
}
```

---

## Billboards (`/api/billboards/`)

### 1) Public list (map/list)

**GET** `/api/billboards/`

**Auth**: not required

**Supported query params (most common)**
- `page`, `page_size`
- `search`
- `ordering` (example: `-created_at`, `views`, `city`)
- `ooh_media_type`
- Map bounds: `ne_lat`, `ne_lng`, `sw_lat`, `sw_lng`
- Radius: `lat`, `lng`, `radius`
- Clustering: `cluster=true`, `zoom=<number>`

**Postman cURL (paginated)**

```bash
curl --location --request GET '{{BASE_URL}}/api/billboards/?page=1&page_size=20&search=Dubai&ordering=-created_at'
```

**Response (200) — paginated**

```json
{
  "links": {
    "next": "http://127.0.0.1:8000/api/billboards/?page=2&page_size=20&search=Dubai&ordering=-created_at",
    "previous": null
  },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 123,
      "city": "Dubai",
      "description": "Large billboard on Sheikh Zayed Road",
      "number_of_boards": "1",
      "average_daily_views": "50000",
      "traffic_direction": "Inbound",
      "road_position": "Left",
      "road_name": "SZR",
      "exposure_time": "10 seconds",
      "price_range": "5000-7000",
      "display_height": "5m",
      "display_width": "15m",
      "advertiser_phone": "+971501234567",
      "advertiser_whatsapp": "+971501234567",
      "company_name": "Media Pro",
      "company_website": "https://mediapro.example",
      "ooh_media_type": "Digital",
      "ooh_media_id": "DB-001",
      "type": "Premium",
      "images": [
        "http://127.0.0.1:8000/media/billboards/img1.jpg",
        "http://127.0.0.1:8000/media/billboards/img2.jpg"
      ],
      "unavailable_dates": [
        "2026-04-01",
        "2026-04-02"
      ],
      "latitude": 25.2048,
      "longitude": 55.2708,
      "views": 10,
      "leads": 2,
      "is_active": true,
      "address": "Sheikh Zayed Road, Dubai",
      "generator_backup": "Yes",
      "created_at": "2026-03-25T10:30:00Z",
      "user_name": "John Doe",
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "approved_at": "2026-03-25T11:00:00Z",
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": "admin",
      "rejected_by_username": null,
      "is_in_wishlist": false
    }
  ]
}
```

---

### 2) Create billboard (media owner only)

**POST** `/api/billboards/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body (JSON)**

```json
{
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [],
  "unavailable_dates": [
    "2026-04-01",
    "2026-04-02"
  ],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/billboards/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [],
  "unavailable_dates": ["2026-04-01","2026-04-02"],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes"
}'
```

**Response (201)**

```json
{
  "id": 123,
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [],
  "unavailable_dates": [
    "2026-04-01",
    "2026-04-02"
  ],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "views": 0,
  "leads": 0,
  "is_active": true,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes",
  "created_at": "2026-03-25T10:30:00Z",
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

**Response (401)**

```json
{
  "detail": "Authentication required to create billboards"
}
```

**Response (403)**

```json
{
  "detail": "Only media owners can create billboards. You are registered as an advertiser."
}
```

---

### 3) Get single billboard (public)

**GET** `/api/billboards/{id}/`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/billboards/123/'
```

**Response (200)**

```json
{
  "id": 123,
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [
    "http://127.0.0.1:8000/media/billboards/img1.jpg",
    "http://127.0.0.1:8000/media/billboards/img2.jpg"
  ],
  "unavailable_dates": [
    "2026-04-01",
    "2026-04-02"
  ],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "views": 10,
  "leads": 2,
  "is_active": true,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes",
  "created_at": "2026-03-25T10:30:00Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-03-25T11:00:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": "admin",
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

**Response (404)**

```json
{
  "detail": "Not found."
}
```

---

### 4) Update billboard (owner media owner only)

**PUT** `/api/billboards/{id}/`

Use this to set availability dates (calendar) by updating `unavailable_dates`.

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body example (set unavailable dates)**

```json
{
  "unavailable_dates": [
    "2026-04-10",
    "2026-04-11",
    "2026-04-12"
  ]
}
```

**Postman cURL**

```bash
curl --location --request PUT '{{BASE_URL}}/api/billboards/123/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "unavailable_dates": ["2026-04-10","2026-04-11","2026-04-12"]
}'
```

**Response (200)** (full billboard object; `unavailable_dates` updated)

```json
{
  "id": 123,
  "city": "Dubai",
  "description": "Large billboard on Sheikh Zayed Road",
  "number_of_boards": "1",
  "average_daily_views": "50000",
  "traffic_direction": "Inbound",
  "road_position": "Left",
  "road_name": "SZR",
  "exposure_time": "10 seconds",
  "price_range": "5000-7000",
  "display_height": "5m",
  "display_width": "15m",
  "advertiser_phone": "+971501234567",
  "advertiser_whatsapp": "+971501234567",
  "company_name": "Media Pro",
  "company_website": "https://mediapro.example",
  "ooh_media_type": "Digital",
  "ooh_media_id": "DB-001",
  "type": "Premium",
  "images": [
    "http://127.0.0.1:8000/media/billboards/img1.jpg",
    "http://127.0.0.1:8000/media/billboards/img2.jpg"
  ],
  "unavailable_dates": [
    "2026-04-10",
    "2026-04-11",
    "2026-04-12"
  ],
  "latitude": 25.2048,
  "longitude": 55.2708,
  "views": 10,
  "leads": 2,
  "is_active": true,
  "address": "Sheikh Zayed Road, Dubai",
  "generator_backup": "Yes",
  "created_at": "2026-03-25T10:30:00Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-03-25T11:00:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": "admin",
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

**Response (403)**

```json
{
  "detail": "You can only update your own billboards."
}
```

---

### 5) Delete billboard (owner media owner only)

**DELETE** `/api/billboards/{id}/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request DELETE '{{BASE_URL}}/api/billboards/123/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (204)**

No response body.

---

### 6) My billboards (media owner only)

**GET** `/api/billboards/my-billboards/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/billboards/my-billboards/?page=1&page_size=20&approval_status=pending' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)** (paginated; items are billboard objects)

```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 123,
      "city": "Dubai",
      "description": "Large billboard on Sheikh Zayed Road",
      "number_of_boards": "1",
      "average_daily_views": "50000",
      "traffic_direction": "Inbound",
      "road_position": "Left",
      "road_name": "SZR",
      "exposure_time": "10 seconds",
      "price_range": "5000-7000",
      "display_height": "5m",
      "display_width": "15m",
      "advertiser_phone": "+971501234567",
      "advertiser_whatsapp": "+971501234567",
      "company_name": "Media Pro",
      "company_website": "https://mediapro.example",
      "ooh_media_type": "Digital",
      "ooh_media_id": "DB-001",
      "type": "Premium",
      "images": [],
      "unavailable_dates": [],
      "latitude": 25.2048,
      "longitude": 55.2708,
      "views": 0,
      "leads": 0,
      "is_active": true,
      "address": "Sheikh Zayed Road, Dubai",
      "generator_backup": "Yes",
      "created_at": "2026-03-25T10:30:00Z",
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

**Response (403)**

```json
{
  "detail": "Only media owners can access their billboards. You are registered as an advertiser."
}
```

---

### 7) Toggle active/inactive (owner media owner only)

**PATCH** `/api/billboards/{id}/toggle-active/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request PATCH '{{BASE_URL}}/api/billboards/123/toggle-active/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "id": "123",
  "is_active": false,
  "message": "Billboard marked as inactive"
}
```

**Response (404)**

```json
{
  "error": "Billboard not found"
}
```

---

### 8) Track view (public)

**POST** `/api/billboards/{id}/track-view/`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/billboards/123/track-view/'
```

**Response (200)**

```json
{
  "message": "View tracked successfully",
  "billboard_id": 123,
  "current_views": 11,
  "owner_view": false,
  "duplicate": false
}
```

**Response (200) — duplicate**

```json
{
  "message": "View already tracked for this billboard",
  "billboard_id": 123,
  "current_views": 11,
  "duplicate": true
}
```

**Response (404)**

```json
{
  "error": "Billboard not found"
}
```

---

### 9) Track view (alias)

**POST** `/api/billboards/{id}/increment-view/`

Same behavior and responses as `/track-view/`.

---

### 10) Track lead (public)

**POST** `/api/billboards/{id}/track-lead/`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/billboards/123/track-lead/'
```

**Response (200)**

```json
{
  "message": "Lead tracked successfully",
  "billboard_id": 123,
  "current_leads": 3,
  "duplicate": false
}
```

**Response (200) — duplicate**

```json
{
  "message": "Lead already tracked for this billboard",
  "billboard_id": 123,
  "current_leads": 3,
  "duplicate": true
}
```

**Response (404)**

```json
{
  "error": "Billboard not found"
}
```

---

## Wishlist (`/api/billboards/wishlist/`) (authenticated)

### 1) List wishlist

**GET** `/api/billboards/wishlist/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/billboards/wishlist/?page=1&page_size=20' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "billboard": {
        "id": 123,
        "city": "Dubai",
        "description": "Large billboard on Sheikh Zayed Road",
        "number_of_boards": "1",
        "average_daily_views": "50000",
        "traffic_direction": "Inbound",
        "road_position": "Left",
        "road_name": "SZR",
        "exposure_time": "10 seconds",
        "price_range": "5000-7000",
        "display_height": "5m",
        "display_width": "15m",
        "advertiser_phone": "+971501234567",
        "advertiser_whatsapp": "+971501234567",
        "company_name": "Media Pro",
        "company_website": "https://mediapro.example",
        "ooh_media_type": "Digital",
        "ooh_media_id": "DB-001",
        "type": "Premium",
        "images": [],
        "unavailable_dates": [],
        "latitude": 25.2048,
        "longitude": 55.2708,
        "views": 10,
        "leads": 2,
        "is_active": true,
        "address": "Sheikh Zayed Road, Dubai",
        "generator_backup": "Yes",
        "created_at": "2026-03-25T10:30:00Z",
        "user_name": "John Doe",
        "approval_status": "approved",
        "approval_status_display": "Approved",
        "approved_at": "2026-03-25T11:00:00Z",
        "rejected_at": null,
        "rejection_reason": null,
        "approved_by_username": "admin",
        "rejected_by_username": null,
        "is_in_wishlist": true
      },
      "created_at": "2026-03-25T12:00:00Z"
    }
  ]
}
```

---

### 2) Add to wishlist

**POST** `/api/billboards/wishlist/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body**

```json
{
  "billboard_id": 123
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/billboards/wishlist/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "billboard_id": 123
}'
```

**Response (201)**

```json
{
  "id": 1,
  "billboard": {
    "id": 123,
    "city": "Dubai",
    "description": "Large billboard on Sheikh Zayed Road",
    "number_of_boards": "1",
    "average_daily_views": "50000",
    "traffic_direction": "Inbound",
    "road_position": "Left",
    "road_name": "SZR",
    "exposure_time": "10 seconds",
    "price_range": "5000-7000",
    "display_height": "5m",
    "display_width": "15m",
    "advertiser_phone": "+971501234567",
    "advertiser_whatsapp": "+971501234567",
    "company_name": "Media Pro",
    "company_website": "https://mediapro.example",
    "ooh_media_type": "Digital",
    "ooh_media_id": "DB-001",
    "type": "Premium",
    "images": [],
    "unavailable_dates": [],
    "latitude": 25.2048,
    "longitude": 55.2708,
    "views": 10,
    "leads": 2,
    "is_active": true,
    "address": "Sheikh Zayed Road, Dubai",
    "generator_backup": "Yes",
    "created_at": "2026-03-25T10:30:00Z",
    "user_name": "John Doe",
    "approval_status": "approved",
    "approval_status_display": "Approved",
    "approved_at": "2026-03-25T11:00:00Z",
    "rejected_at": null,
    "rejection_reason": null,
    "approved_by_username": "admin",
    "rejected_by_username": null,
    "is_in_wishlist": true
  },
  "created_at": "2026-03-25T12:00:00Z"
}
```

**Response (400) — already exists**

```json
{
  "message": "Billboard is already in your wishlist"
}
```

---

### 3) Remove from wishlist

**DELETE** `/api/billboards/wishlist/{billboard_id}/remove/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request DELETE '{{BASE_URL}}/api/billboards/wishlist/123/remove/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "message": "Removed from wishlist successfully"
}
```

**Response (404)**

```json
{
  "message": "Item not found in wishlist"
}
```

---

### 4) Toggle wishlist

**POST** `/api/billboards/wishlist/{billboard_id}/toggle/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/billboards/wishlist/123/toggle/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (201) — added**

```json
{
  "message": "Added to wishlist",
  "in_wishlist": true
}
```

**Response (200) — removed**

```json
{
  "message": "Removed from wishlist",
  "in_wishlist": false
}
```

**Response (404)**

```json
{
  "message": "Billboard not found"
}
```

---

## Notifications (`/api/notifications/`) (authenticated)

### 1) Register device token (FCM)

**POST** `/api/notifications/device-token/register/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body**

```json
{
  "fcm_token": "fcm_token_here",
  "device_type": "android",
  "device_id": "device-123",
  "app_version": "1.0.0",
  "os_version": "14"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/notifications/device-token/register/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "fcm_token": "fcm_token_here",
  "device_type": "android",
  "device_id": "device-123",
  "app_version": "1.0.0",
  "os_version": "14"
}'
```

**Response (201)**

```json
{
  "message": "Device token registered successfully",
  "device_token": {
    "fcm_token": "fcm_token_here",
    "device_type": "android",
    "device_id": "device-123",
    "app_version": "1.0.0",
    "os_version": "14"
  }
}
```

---

### 2) Unregister device token

**POST** `/api/notifications/device-token/unregister/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body**

```json
{
  "fcm_token": "fcm_token_here"
}
```

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/notifications/device-token/unregister/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "fcm_token": "fcm_token_here"
}'
```

**Response (200)**

```json
{
  "message": "Device token unregistered successfully"
}
```

**Response (400)**

```json
{
  "error": "FCM token is required"
}
```

---

### 3) Get notification preferences

**GET** `/api/notifications/preferences/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/notifications/preferences/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "new_leads_enabled": true,
  "new_views_enabled": true,
  "wishlist_updates_enabled": true,
  "system_messages_enabled": true,
  "push_enabled": true,
  "sound_enabled": true,
  "vibration_enabled": true,
  "quiet_hours_enabled": false,
  "quiet_hours_start": null,
  "quiet_hours_end": null
}
```

---

### 4) Update notification preferences

**PATCH** `/api/notifications/preferences/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`
- `Content-Type: application/json`

**Body**

```json
{
  "push_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}
```

**Postman cURL**

```bash
curl --location --request PATCH '{{BASE_URL}}/api/notifications/preferences/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "push_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}'
```

**Response (200)**

```json
{
  "new_leads_enabled": true,
  "new_views_enabled": true,
  "wishlist_updates_enabled": true,
  "system_messages_enabled": true,
  "push_enabled": true,
  "sound_enabled": true,
  "vibration_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}
```

---

### 5) List notifications

**GET** `/api/notifications/notifications/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/notifications/notifications/?page=1&page_size=20' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": "4f9d0f5f-1c2d-4a0b-9d88-111111111111",
      "notification_type": "system_message",
      "notification_type_display": "System Message",
      "title": "Welcome",
      "body": "Welcome to ReachToLet",
      "device_type": "android",
      "device_type_display": "Android",
      "data": {
        "screen": "home"
      },
      "sent_at": "2026-03-25T10:30:00Z",
      "delivered": true,
      "delivered_at": "2026-03-25T10:30:01Z",
      "opened": false,
      "opened_at": null,
      "error_message": null
    }
  ]
}
```

---

### 6) Mark one notification opened

**POST** `/api/notifications/notifications/{notification_id}/mark-opened/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/notifications/notifications/4f9d0f5f-1c2d-4a0b-9d88-111111111111/mark-opened/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "message": "Notification marked as opened"
}
```

---

### 7) Mark all notifications opened

**POST** `/api/notifications/notifications/mark-all-opened/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/notifications/notifications/mark-all-opened/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "message": "All notifications marked as opened"
}
```

---

### 8) Notification stats

**GET** `/api/notifications/stats/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request GET '{{BASE_URL}}/api/notifications/stats/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "total_notifications": 10,
  "unread_notifications": 3,
  "delivered_notifications": 10,
  "failed_notifications": 0,
  "notifications_by_type": {
    "system_message": 10
  }
}
```

---

### 9) Test notification

**POST** `/api/notifications/test/`

**Headers**
- `Authorization: Bearer {{ACCESS_TOKEN}}`

**Postman cURL**

```bash
curl --location --request POST '{{BASE_URL}}/api/notifications/test/' \
--header 'Authorization: Bearer {{ACCESS_TOKEN}}'
```

**Response (200)**

```json
{
  "message": "Test notification sent successfully",
  "notification_count": 1
}
```

**Response (400)**

```json
{
  "error": "No active device tokens found. Please register your device first."
}
```

---

## Excluded (admin only)

- `/api/admin-panel/*`
- `/api/billboards/pending/`
- `/api/billboards/{id}/approval-status/`
- `/api/notifications/send/`

