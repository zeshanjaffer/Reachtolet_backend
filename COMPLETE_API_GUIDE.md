# Reachtolet Complete API Guide

Full REST API reference for the **website / mobile app** (Next.js, Flutter, etc.).

**Base URL:** `http://16.16.160.64:8000`  
**Socket.IO URL:** `http://16.16.160.64:8000` (path `/socket.io/`)

**Excluded from this guide:** `/api/admin-panel/*`, Django `/admin/`, staff-only billboard approval endpoints, and admin notification send.

---

## Table of contents

1. [Authentication](#authentication)
2. [Response formats](#response-formats)
3. [HTTP status codes](#http-status-codes)
4. [Users API](#users-api)
5. [Billboards API](#billboards-api)
6. [Chat REST API](#chat-rest-api)
7. [Chat Socket.IO](#chat-socketio)
8. [Notifications API](#notifications-api)
9. [Search & filter API](#search--filter-api)
10. [Endpoint index](#endpoint-index)

---

## Authentication

Most endpoints require a JWT access token:

```http
Authorization: Bearer {access_token}
```

| Token | Lifetime | Usage |
|---|---|---|
| `access` | ~5 min (SimpleJWT default) | Every authenticated API call |
| `refresh` | ~1 day | `POST /api/users/token/refresh/` to get a new access token |

Obtain tokens via **register**, **login**, or **google-login**. Store both tokens client-side; clear on logout.

---

## Response formats

### Auth responses (`login`, `register`, `refresh`, `google-login`)

```json
{
  "status_code": 200,
  "message": "Logged in successfully",
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 17,
    "email": "user@example.com",
    "user_type": "advertiser"
  }
}
```

Register also returns `full_name`, `phone`, `country_code` inside `user`.

### Action responses (many POST/PATCH/DELETE endpoints)

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

### Paginated list responses

```json
{
  "links": { "next": null, "previous": null },
  "count": 42,
  "total_pages": 3,
  "current_page": 1,
  "results": []
}
```

Query params: `page` (default 1), `page_size` (default 20, max 100).

### Validation errors (DRF)

```json
{
  "email": ["This field is required."],
  "password": ["This field is required."]
}
```

Or a single detail:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## HTTP status codes

| Code | Meaning | When you see it |
|---|---|---|
| **200** | OK | Successful GET, PUT, PATCH, or idempotent POST |
| **201** | Created | Register, create billboard, send message, add wishlist |
| **204** | No Content | Delete billboard (empty body) |
| **400** | Bad Request | Validation failed, duplicate wishlist, invalid dates |
| **401** | Unauthorized | Missing/invalid/expired JWT, bad login, logout without credentials |
| **403** | Forbidden | Wrong role (advertiser creating billboard, etc.) |
| **404** | Not Found | Billboard, room, or message does not exist |
| **500** | Server Error | Upload failure, unexpected exception |

---

## Users API

Prefix: `/api/users/`

### Health check

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/users/health/` |
| **Auth** | None |

```bash
curl --location "http://16.16.160.64:8000/api/users/health/"
```

**200 OK**

```json
{
  "status": "healthy",
  "timestamp": "2026-06-13T13:48:15.059092",
  "message": "Users backend is running"
}
```

---

### Register

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/register/` |
| **Auth** | None |
| **Content-Type** | `application/json` |

**Body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | Yes | Unique |
| `password` | string | Yes | Django password rules |
| `full_name` | string | Yes | |
| `phone` | string | Yes | E.164, e.g. `+923001234567` |
| `country_code` | string | Yes | ISO 3166-1 alpha-2, e.g. `PK` |
| `user_type` | string | Yes | `advertiser` or `media_owner` (immutable after signup) |

```bash
curl --location "http://16.16.160.64:8000/api/users/register/" \
  --header "Content-Type: application/json" \
  --data '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Doe",
    "phone": "+923001234567",
    "country_code": "PK",
    "user_type": "advertiser"
  }'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "User registered successfully",
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 25,
    "email": "newuser@example.com",
    "full_name": "Jane Doe",
    "phone": "+923001234567",
    "country_code": "PK",
    "user_type": "advertiser"
  }
}
```

**400 Bad Request** — invalid phone, country code, duplicate email, weak password.

---

### Login

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/login/` |
| **Auth** | None |

**Body:** `{ "email": "...", "password": "..." }`

```bash
curl --location "http://16.16.160.64:8000/api/users/login/" \
  --header "Content-Type: application/json" \
  --data '{"email": "admin@gmail.com", "password": "your_password"}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Logged in successfully",
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 17,
    "email": "admin@gmail.com",
    "user_type": "advertiser"
  }
}
```

**401 Unauthorized**

```json
{
  "detail": ["No active account found with the given credentials"]
}
```

---

### Refresh token

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/token/refresh/` |
| **Auth** | None |

**Body:** `{ "refresh": "eyJ..." }`

```bash
curl --location "http://16.16.160.64:8000/api/users/token/refresh/" \
  --header "Content-Type: application/json" \
  --data '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Token refreshed successfully",
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

**401 Unauthorized** — invalid or blacklisted refresh token.

---

### Logout

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/logout/` |
| **Auth** | Optional Bearer and/or refresh in body |

**Body (optional):** `{ "refresh": "eyJ..." }`

```bash
curl --location "http://16.16.160.64:8000/api/users/logout/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Logged out successfully"
}
```

**401 Unauthorized** — no valid Bearer token and no refresh token provided.

---

### Validate token

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/users/validate-token/` |
| **Auth** | Bearer required |

```bash
curl --location "http://16.16.160.64:8000/api/users/validate-token/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "valid": true,
  "user": {
    "id": 17,
    "email": "admin@gmail.com",
    "user_type": "advertiser"
  }
}
```

**401 Unauthorized** — expired or missing token.

---

### Get profile

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/users/profile/` |
| **Auth** | Bearer required |

```bash
curl --location "http://16.16.160.64:8000/api/users/profile/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "id": 17,
  "email": "admin@gmail.com",
  "phone": "+10000000000",
  "country_code": "US",
  "formatted_phone": "US +10000000000",
  "full_name": "admin",
  "profile_image": null,
  "user_type": "advertiser"
}
```

---

### Update profile

| | |
|---|---|
| **Method** | `PUT` |
| **Path** | `/api/users/profile/` |
| **Auth** | Bearer required |

**Editable:** `phone`, `country_code`, `full_name`, `profile_image`  
**Read-only:** `id`, `email`, `user_type`

```bash
curl --location --request PUT "http://16.16.160.64:8000/api/users/profile/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{
    "full_name": "Jane Updated",
    "phone": "+923001234567",
    "country_code": "PK"
  }'
```

**200 OK** — same shape as GET profile.

**400 Bad Request** — invalid phone/country or attempt to change `user_type`.

---

### Upload profile image

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/upload-profile-image/` |
| **Auth** | Bearer required |
| **Content-Type** | `multipart/form-data` |

**Field:** `image` (jpeg/png/gif/webp, max 5 MB)

```bash
curl --location "http://16.16.160.64:8000/api/users/upload-profile-image/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --form 'image=@"/path/to/photo.jpg"'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "Profile image uploaded successfully"
}
```

**400 Bad Request** — no file, wrong type, or file too large.

---

### Google login

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/users/google-login/` |
| **Auth** | None |

**Body**

| Field | Required | Notes |
|---|---|---|
| `id_token` | Yes | Google OAuth ID token |
| `user_type` | No | `advertiser` (default) or `media_owner` for **new** users only |

```bash
curl --location "http://16.16.160.64:8000/api/users/google-login/" \
  --header "Content-Type: application/json" \
  --data '{
    "id_token": "GOOGLE_ID_TOKEN",
    "user_type": "advertiser"
  }'
```

**200 OK** — same auth response shape as login.

**400 Bad Request** — missing token, invalid token, invalid audience, no email in token.

---

### Country codes

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/users/country-codes/` |
| **Auth** | None |

```bash
curl --location "http://16.16.160.64:8000/api/users/country-codes/"
```

**200 OK**

```json
{
  "countries": [
    { "code": "PK", "name": "Pakistan", "dial_code": "+92" },
    { "code": "US", "name": "United States", "dial_code": "+1" }
  ],
  "total": 195
}
```

**500 Internal Server Error**

```json
{
  "error": "Failed to get country codes"
}
```

---

## Billboards API

Prefix: `/api/billboards/`  
**Auth:** Bearer required on all endpoints below.

User roles:

| Role | Capabilities |
|---|---|
| `advertiser` | Map, preview, detail, wishlist, track view/lead, start chat |
| `media_owner` | Create/update/delete own billboards, my-billboards, availability, toggle active |

Public map only shows billboards with `is_active=true` and `approval_status=approved`.

---

### List billboards (map / search / filter)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/` |

> **Full search & filter reference:** see [`BILLBOARD_SEARCH_FILTER_API_GUIDE.md`](BILLBOARD_SEARCH_FILTER_API_GUIDE.md) — every parameter, curl, response shape, and status code for public list, my-billboards, and wishlist.

**Query parameters**

| Param | Description |
|---|---|
| `search` | Text search: `city`, `description`, `company_name`, `road_name` (partial, case-insensitive) |
| `ooh_media_type` | Filter: `Digital Billboard` or `Static Billboard` (case-insensitive exact) |
| `cluster` | `true` to enable Supercluster map clustering |
| `zoom` | Map zoom 0–20 (default `10`) |
| `ne_lat`, `ne_lng`, `sw_lat`, `sw_lng` | Map bounds; disables pagination |
| `lat`, `lng`, `radius` | Radius filter in km (when bounds not set) |
| `ordering` | `created_at`, `price_range`, `city`, `views` (prefix `-` for desc) |
| `page`, `page_size` | Pagination (when no map bounds) |

#### Map with clustering

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?cluster=true&zoom=10&ne_lat=35&ne_lng=77&sw_lat=28&sw_lng=70" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "count": 2,
  "clustered_count": 2,
  "clusters": [
    {
      "type": "marker",
      "id": 40,
      "latitude": 31.52,
      "longitude": 74.35,
      "count": 1
    },
    {
      "type": "cluster",
      "cluster_id": 1,
      "latitude": 31.45,
      "longitude": 74.26,
      "count": 5,
      "expansion_zoom": 12
    }
  ],
  "clustering_enabled": true,
  "zoom_level": 10.0
}
```

#### Map without clustering

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ne_lat=35&ne_lng=77&sw_lat=28&sw_lng=70" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "count": 2,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ],
  "clustering_enabled": false
}
```

#### Paginated list (no bounds)

**200 OK** — paginated format; each result: `{ "id", "latitude", "longitude", "count": 1 }`.

---

### Billboard preview (map pin tap)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/{billboard_id}/preview/` |

Lightweight card before full detail page. See also `BILLBOARD_PREVIEW_API_GUIDE.md`.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/40/preview/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "id": 40,
  "city": "TestCity",
  "road_name": null,
  "image": null,
  "price": {
    "amount": "8000",
    "currency": "PKR",
    "period": "per month"
  },
  "display_size": {
    "width": null,
    "height": null,
    "unit": "meters",
    "label": null
  },
  "views_per_day": null,
  "availability": {
    "status": "available",
    "label": "Available",
    "total_booked": 0
  },
  "lighting": {
    "has_lighting": false,
    "label": "No lighting"
  },
  "is_in_wishlist": false
}
```

**404 Not Found** — billboard not visible to this user.

---

### Billboard detail

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/{id}/` |

```bash
curl --location "http://16.16.160.64:8000/api/billboards/40/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "id": 40,
  "city": "TestCity",
  "description": null,
  "number_of_boards": null,
  "average_daily_views": null,
  "traffic_direction": null,
  "road_position": null,
  "road_name": null,
  "exposure_time": null,
  "price_range": "8000",
  "display_height": null,
  "display_width": null,
  "advertiser_phone": null,
  "advertiser_whatsapp": null,
  "company_name": null,
  "company_website": null,
  "ooh_media_type": "Digital Billboard",
  "ooh_media_id": null,
  "type": "Premium",
  "images": [],
  "specifications": {
    "currency": "PKR",
    "price_per_second": 800,
    "loop_duration_seconds": 60,
    "allowed_video_lengths": [10, 20, 30],
    "slots": [
      { "slot_number": 1, "duration_seconds": 10, "status": "booked" }
    ]
  },
  "availability": {
    "booked_dates": [],
    "total_booked": 0
  },
  "latitude": 31.52,
  "longitude": 74.35,
  "views": 0,
  "leads": 0,
  "is_active": true,
  "address": null,
  "generator_backup": null,
  "created_at": "2026-06-13T10:41:51.409481Z",
  "user_name": "",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-06-13T10:41:51.408984Z",
  "rejected_at": null,
  "rejection_reason": null,
  "is_in_wishlist": false
}
```

**404 Not Found**

---

### Create billboard

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/billboards/` |
| **Role** | `media_owner` only |
| **Content-Type** | `multipart/form-data` |

Send `specifications` as a **JSON string**. Use `ooh_media_type`: `Digital Billboard` or `Static Billboard`.  
See `BILLBOARD_SPECIFICATIONS_GUIDE.md` for specification shapes.

**Common form fields:** `city`, `latitude`, `longitude`, `price_range`, `ooh_media_type`, `type`, `description`, `specifications`, `images_0`, `images_1`, …

```bash
curl --location "http://16.16.160.64:8000/api/billboards/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'city="Lahore"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'price_range="8000"' \
  --form 'ooh_media_type="Digital Billboard"' \
  --form 'type="Premium"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_second\":800,\"loop_duration_seconds\":60,\"allowed_video_lengths\":[10,20,30],\"slots\":[]}"' \
  --form 'images_0=@"/path/to/photo.jpg"'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

**401 Unauthorized** — not logged in.

**403 Forbidden**

```json
{
  "detail": "Only media owners can create billboards. You are registered as an advertiser."
}
```

**400 Bad Request** — validation errors or invalid image type/size.

---

### Update billboard

| | |
|---|---|
| **Method** | `PUT` / `PATCH` |
| **Path** | `/api/billboards/{id}/` |
| **Role** | Owner `media_owner` only |

Do **not** send `booked_dates`, `unavailable_dates`, or `availability` here — use the availability endpoint.

```bash
curl --location --request PATCH "http://16.16.160.64:8000/api/billboards/40/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'price_range="9000"' \
  --form 'description="Updated description"'
```

**200 OK** — full billboard object (same as GET detail).

**403 Forbidden** — not owner or not media owner.

---

### Delete billboard

| | |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/api/billboards/{id}/` |
| **Role** | Owner `media_owner` only |

```bash
curl --location --request DELETE "http://16.16.160.64:8000/api/billboards/40/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**204 No Content** — empty body.

**403 Forbidden** / **404 Not Found**

---

### My billboards

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/my-billboards/` |
| **Role** | `media_owner` only |

**Search:** `search` (city, description, company_name)  
**Filters:** `city`, `ooh_media_type`, `type`, `is_active`, `approval_status`  
**Sort / page:** `ordering`, `page`, `page_size`

See [`BILLBOARD_SEARCH_FILTER_API_GUIDE.md`](BILLBOARD_SEARCH_FILTER_API_GUIDE.md) §2 for every filter curl and response.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?search=Test&ooh_media_type=Digital%20Billboard&is_active=true&approval_status=approved" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK** — paginated list; each item is full billboard shape (same fields as detail).

**403 Forbidden**

```json
{
  "detail": "Only media owners can access their billboards. You are registered as an advertiser."
}
```

---

### Toggle active status

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/api/billboards/{billboard_id}/toggle-active/` |
| **Role** | Owner `media_owner` |

```bash
curl --location --request PATCH "http://16.16.160.64:8000/api/billboards/40/toggle-active/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK**

```json
{
  "id": "40",
  "is_active": false,
  "message": "Billboard marked as inactive"
}
```

**403 Forbidden** / **404 Not Found**

---

### Availability

| | |
|---|---|
| **GET** | `/api/billboards/{billboard_id}/availability/` |
| **PUT** | Same path — owner sets booked dates |

#### GET availability

**Query (optional):** `from=YYYY-MM-DD`, `to=YYYY-MM-DD`

```bash
curl --location "http://16.16.160.64:8000/api/billboards/40/availability/?from=2026-06-01&to=2026-06-30" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "billboard_id": 40,
  "booked_dates": ["2026-06-15", "2026-06-16"],
  "total_booked": 2,
  "from": "2026-06-01",
  "to": "2026-06-30"
}
```

**400 Bad Request** — invalid date format or `from > to`.  
**404 Not Found**

#### PUT availability (media owner, own billboard)

```bash
curl --location --request PUT "http://16.16.160.64:8000/api/billboards/40/availability/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"booked_dates": ["2026-06-15", "2026-06-20"]}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Availability updated successfully",
  "billboard_id": 40,
  "booked_dates": ["2026-06-15", "2026-06-20"],
  "total_booked": 2
}
```

**403 Forbidden** — not media owner or not billboard owner.

---

### Track view

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/billboards/{billboard_id}/track-view/` |
| **Alias** | `/api/billboards/{billboard_id}/increment-view/` |

One view per user per billboard. Owner views are not counted.

```bash
curl --location --request POST "http://16.16.160.64:8000/api/billboards/40/track-view/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{ "status_code": 200, "message": "View tracked successfully" }
```

Also **200** with `"View already tracked..."` or `"View not tracked - owner viewing own billboard"`.

**404 Not Found** / **500 Internal Server Error**

---

### Track lead

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/billboards/{billboard_id}/track-lead/` |

Call when user taps phone/WhatsApp. Same dedup rules as views.

```bash
curl --location --request POST "http://16.16.160.64:8000/api/billboards/40/track-lead/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{ "status_code": 200, "message": "Lead tracked successfully" }
```

**404 Not Found** / **500 Internal Server Error**

---

### Wishlist — list

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/wishlist/` |

**Search:** `search` (billboard city, description, company_name)  
**Sort:** `ordering` (`created_at`, `-created_at`)

See [`BILLBOARD_SEARCH_FILTER_API_GUIDE.md`](BILLBOARD_SEARCH_FILTER_API_GUIDE.md) §3.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/wishlist/?search=Lahore&ordering=-created_at" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — paginated; each result:

```json
{
  "id": 1,
  "billboard": { "...full billboard object..." },
  "created_at": "2026-06-13T12:00:00Z"
}
```

---

### Wishlist — add

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/billboards/wishlist/` |

**Body:** `{ "billboard_id": 40 }`

```bash
curl --location --request POST "http://16.16.160.64:8000/api/billboards/wishlist/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"billboard_id": 40}'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "Added to wishlist successfully"
}
```

**400 Bad Request** — already in wishlist or invalid billboard_id.

---

### Wishlist — remove

| | |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/api/billboards/wishlist/{billboard_id}/remove/` |

```bash
curl --location --request DELETE "http://16.16.160.64:8000/api/billboards/wishlist/40/remove/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{ "message": "Removed from wishlist successfully" }
```

**404 Not Found**

```json
{ "message": "Item not found in wishlist" }
```

---

### Wishlist — toggle

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/billboards/wishlist/{billboard_id}/toggle/` |

```bash
curl --location --request POST "http://16.16.160.64:8000/api/billboards/wishlist/40/toggle/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — removed:

```json
{ "status_code": 200, "message": "Removed from wishlist" }
```

**201 Created** — added:

```json
{ "status_code": 201, "message": "Added to wishlist" }
```

**404 Not Found** — billboard does not exist.

---

## Chat REST API

Prefix: `/api/chat/`  
**Auth:** Bearer required on all endpoints.

One chat room per `(billboard, advertiser)`. Media owner is the billboard owner.  
See `BILLBOARD_CHAT_GUIDE.md` for full flow.

Message statuses: `sent` → `delivered` → `seen`.

---

### Unread summary (badge)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/chat/unread/` |

Works for both advertiser and media owner.

```bash
curl --location "http://16.16.160.64:8000/api/chat/unread/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "total_unread": 3,
  "rooms_with_unread": 2,
  "rooms": [
    { "room_id": 1, "unread_count": 2 },
    { "room_id": 5, "unread_count": 1 }
  ]
}
```

---

### List chat rooms

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/chat/rooms/` |

```bash
curl --location "http://16.16.160.64:8000/api/chat/rooms/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — paginated:

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "billboard_id": 40,
      "billboard": {
        "id": 40,
        "city": "TestCity",
        "road_name": null,
        "ooh_media_type": "Digital Billboard",
        "image": null
      },
      "advertiser_id": 17,
      "media_owner_id": 21,
      "other_user": {
        "id": 21,
        "email": "owner@example.com",
        "full_name": "Media Owner",
        "user_type": "media_owner"
      },
      "last_message": {
        "id": 1,
        "room_id": 1,
        "sender_id": 17,
        "sender_email": "admin@gmail.com",
        "sender_name": "admin",
        "body": "Hello, is this billboard available next week?",
        "message_type": "text",
        "status": "sent",
        "attachments": [],
        "created_at": "2026-06-13T11:28:46.957507+00:00"
      },
      "unread_count": 0,
      "created_at": "2026-06-13T11:28:39.578231+00:00",
      "updated_at": "2026-06-13T11:28:47.315893+00:00"
    }
  ]
}
```

---

### Create room (POST)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/chat/rooms/` |
| **Role** | `advertiser` |

**Body:** `{ "billboard_id": 40 }`

```bash
curl --location --request POST "http://16.16.160.64:8000/api/chat/rooms/" \
  --header "Authorization: Bearer ADVERTISER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"billboard_id": 40}'
```

**201 Created** — new room:

```json
{
  "status_code": 201,
  "message": "Chat room created",
  "room": { "...room object..." }
}
```

**200 OK** — room already exists:

```json
{
  "status_code": 200,
  "message": "Chat room already exists",
  "room": { "...room object..." }
}
```

**403 Forbidden** — not advertiser.  
**404 Not Found** — billboard not found.  
**400 Bad Request** — no media owner on billboard, or chatting on own billboard.

---

### Get or create room by billboard (Message button)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/chat/rooms/by-billboard/{billboard_id}/` |
| **Role** | `advertiser` only |

```bash
curl --location "http://16.16.160.64:8000/api/chat/rooms/by-billboard/40/" \
  --header "Authorization: Bearer ADVERTISER_TOKEN"
```

**201 Created** / **200 OK** — same shape as POST `/rooms/`.

**403 Forbidden**

```json
{
  "status_code": 403,
  "message": "Only advertisers can open chat from a billboard detail screen."
}
```

---

### Room detail

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/chat/rooms/{room_id}/` |

```bash
curl --location "http://16.16.160.64:8000/api/chat/rooms/1/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — single room object (same shape as list item).

**403 Forbidden** — not a participant.  
**404 Not Found**

---

### List messages

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/chat/rooms/{room_id}/messages/` |

Oldest-first within each page.

```bash
curl --location "http://16.16.160.64:8000/api/chat/rooms/1/messages/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — paginated:

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "room_id": 1,
      "sender_id": 17,
      "sender_email": "admin@gmail.com",
      "sender_name": "admin",
      "body": "Hello, is this billboard available next week?",
      "message_type": "text",
      "status": "sent",
      "attachments": [],
      "created_at": "2026-06-13T11:28:46.957507+00:00"
    }
  ]
}
```

`message_type`: `text`, `attachment`, or `mixed`.  
Attachment object: `{ "id", "original_name", "content_type", "file_size", "url" }`.

---

### Send message

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/chat/rooms/{room_id}/messages/` |
| **Content-Type** | `multipart/form-data` or JSON |

**Fields:** `body` (optional if attachments present), `attachment_0`, `file_0`, … (max 15 MB each)

```bash
# Text only
curl --location --request POST "http://16.16.160.64:8000/api/chat/rooms/1/messages/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --form 'body="Is it still available?"'

# With attachment
curl --location --request POST "http://16.16.160.64:8000/api/chat/rooms/1/messages/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --form 'body="Please see attached brief"' \
  --form 'attachment_0=@"/path/to/brief.pdf"'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "Message sent",
  "message_data": {
    "id": 2,
    "room_id": 1,
    "sender_id": 17,
    "sender_email": "admin@gmail.com",
    "sender_name": "admin",
    "body": "Is it still available?",
    "message_type": "text",
    "status": "sent",
    "attachments": [],
    "created_at": "2026-06-13T12:00:00+00:00"
  }
}
```

**400 Bad Request** — empty body and no attachments, or disallowed file type.

---

### Mark messages read (seen)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/chat/rooms/{room_id}/read/` |

**Body:** `{ "message_id": 5 }` — marks all messages up to and including this id as seen.

```bash
curl --location --request POST "http://16.16.160.64:8000/api/chat/rooms/1/read/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"message_id": 5}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Messages marked as read",
  "message_id": 5,
  "status": "seen"
}
```

**404 Not Found** — message not in room.

---

### Mark message delivered

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/chat/rooms/{room_id}/messages/{message_id}/delivered/` |

```bash
curl --location --request POST "http://16.16.160.64:8000/api/chat/rooms/1/messages/5/delivered/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "message_id": 5,
  "status": "delivered"
}
```

**404 Not Found**

---

## Chat Socket.IO

**URL:** `http://16.16.160.64:8000`  
**Path:** `/socket.io/`  
**Server:** Daphne ASGI (required for WebSockets)

### Connect

Pass JWT as `auth.token` or query `?token=ACCESS_TOKEN`.

```javascript
import { io } from 'socket.io-client';

const socket = io('http://16.16.160.64:8000', {
  auth: { token: accessToken },
  transports: ['websocket', 'polling'],
});

socket.on('connected', (data) => {
  // { user_id: 17 }
});

socket.on('error', (data) => {
  // { message: "...", status_code: 401 }
});
```

Invalid token → connection rejected.

### Client → server events

| Event | Payload | Description |
|---|---|---|
| `join_room` | `{ "room_id": 1 }` | Subscribe to room channel |
| `leave_room` | `{ "room_id": 1 }` | Unsubscribe |
| `typing_start` | `{ "room_id": 1 }` | Typing indicator on |
| `typing_stop` | `{ "room_id": 1 }` | Typing indicator off |
| `send_message` | `{ "room_id": 1, "body": "Hi" }` | Text only (prefer REST for files) |
| `message_delivered` | `{ "room_id": 1, "message_id": 5 }` | Mark delivered |
| `messages_seen` | `{ "room_id": 1, "message_id": 5 }` | Mark seen |

### Server → client events

| Event | Payload |
|---|---|
| `connected` | `{ "user_id": 17 }` |
| `room_joined` | `{ "room_id": 1 }` |
| `room_left` | `{ "room_id": 1 }` |
| `new_message` | Full message object (same as REST `message_data`) |
| `user_typing` | `{ "room_id", "user_id", "user_name", "is_typing" }` |
| `message_delivered` | `{ "room_id", "message_id", "user_id", "status" }` |
| `messages_seen` | `{ "room_id", "message_id", "user_id", "status": "seen" }` |
| `error` | `{ "message", "status_code" }` |

### Recommended flow

1. Open chat → REST `GET .../messages/` for history  
2. Connect socket → `join_room`  
3. Send via REST POST (supports attachments) → receive `new_message` on socket  
4. On receive → emit `message_delivered`  
5. When chat visible → REST `POST .../read/` or socket `messages_seen`

---

## Notifications API

Prefix: `/api/notifications/`  
**Auth:** Bearer required on all endpoints below.

---

### Register device token (FCM)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/notifications/device-token/register/` |

**Body**

| Field | Required | Notes |
|---|---|---|
| `fcm_token` | Yes | Firebase token |
| `device_type` | No | `android` (default), `ios`, `web` |
| `device_id` | No | |
| `app_version` | No | |
| `os_version` | No | |

```bash
curl --location --request POST "http://16.16.160.64:8000/api/notifications/device-token/register/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{
    "fcm_token": "FCM_TOKEN_HERE",
    "device_type": "android",
    "device_id": "device-uuid-123"
  }'
```

**201 Created**

```json
{
  "status_code": 201,
  "message": "Device token registered successfully"
}
```

**400 Bad Request** — registration failed.

---

### Unregister device token

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/notifications/device-token/unregister/` |

**Body:** `{ "fcm_token": "..." }`

```bash
curl --location --request POST "http://16.16.160.64:8000/api/notifications/device-token/unregister/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"fcm_token": "FCM_TOKEN_HERE"}'
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Device token unregistered successfully"
}
```

**400 Bad Request** — missing `fcm_token` or token not found.

---

### Notification preferences

| | |
|---|---|
| **GET** | `/api/notifications/preferences/` |
| **PUT/PATCH** | Same path |

```bash
curl --location "http://16.16.160.64:8000/api/notifications/preferences/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

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

**PATCH example**

```bash
curl --location --request PATCH "http://16.16.160.64:8000/api/notifications/preferences/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"push_enabled": false, "quiet_hours_enabled": true, "quiet_hours_start": "22:00", "quiet_hours_end": "08:00"}'
```

---

### List notifications

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/notifications/notifications/` |

**Query:** `limit` (default 50), `offset` (default 0), `page`, `page_size`

```bash
curl --location "http://16.16.160.64:8000/api/notifications/notifications/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — paginated:

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "notification_type": "new_lead",
      "notification_type_display": "New Lead",
      "title": "New lead on your billboard",
      "body": "Someone contacted you about Lahore Premium Board",
      "device_type": "android",
      "device_type_display": "Android",
      "data": { "billboard_id": 40 },
      "sent_at": "2026-06-13T10:00:00Z",
      "delivered": true,
      "delivered_at": "2026-06-13T10:00:01Z",
      "opened": false,
      "opened_at": null,
      "error_message": null
    }
  ]
}
```

---

### Mark notification opened

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/notifications/notifications/{notification_id}/mark-opened/` |

`notification_id` is a UUID.

```bash
curl --location --request POST "http://16.16.160.64:8000/api/notifications/notifications/550e8400-e29b-41d4-a716-446655440000/mark-opened/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Notification marked as opened"
}
```

**400 Bad Request** — notification not found for user.

---

### Mark all notifications opened

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/notifications/notifications/mark-all-opened/` |

```bash
curl --location --request POST "http://16.16.160.64:8000/api/notifications/notifications/mark-all-opened/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "All notifications marked as opened"
}
```

**500 Internal Server Error**

---

### Notification stats

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/notifications/stats/` |

```bash
curl --location "http://16.16.160.64:8000/api/notifications/stats/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "total_notifications": 12,
  "unread_notifications": 3,
  "delivered_notifications": 11,
  "failed_notifications": 1,
  "notifications_by_type": {
    "new_lead": 2,
    "new_view": 5,
    "wishlist_added": 0,
    "billboard_activated": 1,
    "billboard_deactivated": 0,
    "billboard_approved": 1,
    "billboard_rejected": 0,
    "price_update": 0,
    "system_message": 2,
    "welcome": 1
  }
}
```

---

### Test notification (optional)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/notifications/test/` |

Sends a test push to the current user's registered devices.

```bash
curl --location --request POST "http://16.16.160.64:8000/api/notifications/test/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "Test notification sent successfully"
}
```

**400 Bad Request** — no registered device tokens.

---

## Search & filter API

Search and filter are **query parameters** on list endpoints (not separate URLs).

| Endpoint | Search param | Filter params | Response |
|---|---|---|---|
| `GET /api/billboards/` | `search` | `ooh_media_type`, bounds, radius | Minimal markers or clusters |
| `GET /api/billboards/my-billboards/` | `search` | `city`, `ooh_media_type`, `type`, `is_active`, `approval_status` | Full billboard objects |
| `GET /api/billboards/wishlist/` | `search` | — (sort only) | Wishlist items with nested billboard |

**Complete guide with all curls, filter types, combined examples, and status codes:**

→ **[BILLBOARD_SEARCH_FILTER_API_GUIDE.md](BILLBOARD_SEARCH_FILTER_API_GUIDE.md)**

---

## Endpoint index

### Users — `/api/users/`

| Method | Path | Auth | Status codes |
|---|---|---|---|
| GET | `/health/` | No | 200 |
| POST | `/register/` | No | 201, 400 |
| POST | `/login/` | No | 200, 401 |
| POST | `/token/refresh/` | No | 200, 401 |
| POST | `/logout/` | Optional | 200, 401 |
| GET | `/validate-token/` | Yes | 200, 401 |
| GET | `/country-codes/` | No | 200, 500 |
| GET | `/profile/` | Yes | 200, 401 |
| PUT | `/profile/` | Yes | 200, 400, 401 |
| POST | `/upload-profile-image/` | Yes | 201, 400, 401, 500 |
| POST | `/google-login/` | No | 200, 400 |

### Billboards — `/api/billboards/`

| Method | Path | Role | Status codes |
|---|---|---|---|
| GET | `/` | Any | 200, 401 |
| POST | `/` | media_owner | 201, 400, 401, 403 |
| GET | `/my-billboards/` | media_owner | 200, 401, 403 |
| GET | `/{id}/preview/` | Any | 200, 401, 404 |
| GET | `/{id}/` | Any | 200, 401, 404 |
| PUT/PATCH | `/{id}/` | owner | 200, 400, 401, 403, 404 |
| DELETE | `/{id}/` | owner | 204, 401, 403, 404 |
| PATCH | `/{id}/toggle-active/` | owner | 200, 401, 403, 404, 500 |
| GET | `/{id}/availability/` | Any | 200, 400, 401, 404 |
| PUT | `/{id}/availability/` | owner | 200, 400, 401, 403, 404 |
| POST | `/{id}/track-view/` | Any | 200, 401, 404, 500 |
| POST | `/{id}/track-lead/` | Any | 200, 401, 404, 500 |
| GET | `/wishlist/` | Any | 200, 401 |
| POST | `/wishlist/` | Any | 201, 400, 401 |
| DELETE | `/wishlist/{id}/remove/` | Any | 200, 401, 404 |
| POST | `/wishlist/{id}/toggle/` | Any | 200, 201, 401, 404 |

### Chat — `/api/chat/`

| Method | Path | Role | Status codes |
|---|---|---|---|
| GET | `/unread/` | Any | 200, 401 |
| GET | `/rooms/` | Any | 200, 401 |
| POST | `/rooms/` | advertiser | 200, 201, 400, 401, 403, 404 |
| GET | `/rooms/by-billboard/{id}/` | advertiser | 200, 201, 401, 403, 404 |
| GET | `/rooms/{id}/` | participant | 200, 401, 403, 404 |
| GET | `/rooms/{id}/messages/` | participant | 200, 401, 403, 404 |
| POST | `/rooms/{id}/messages/` | participant | 201, 400, 401, 403, 404 |
| POST | `/rooms/{id}/read/` | participant | 200, 401, 403, 404 |
| POST | `/rooms/{id}/messages/{msg_id}/delivered/` | participant | 200, 401, 403, 404 |

### Notifications — `/api/notifications/`

| Method | Path | Status codes |
|---|---|---|
| POST | `/device-token/register/` | 201, 400, 401 |
| POST | `/device-token/unregister/` | 200, 400, 401 |
| GET/PATCH | `/preferences/` | 200, 401 |
| GET | `/notifications/` | 200, 401 |
| POST | `/notifications/{uuid}/mark-opened/` | 200, 400, 401 |
| POST | `/notifications/mark-all-opened/` | 200, 401, 500 |
| GET | `/stats/` | 200, 401, 500 |
| POST | `/test/` | 200, 400, 401, 500 |

---

## Related guides

| File | Topic |
|---|---|
| `BILLBOARD_SEARCH_FILTER_API_GUIDE.md` | Search & filter params, curls, all response shapes |
| `BILLBOARD_PREVIEW_API_GUIDE.md` | Map pin preview field details |
| `BILLBOARD_SPECIFICATIONS_GUIDE.md` | Digital/static `specifications` JSON |
| `BILLBOARD_CHAT_GUIDE.md` | Chat flow, Flutter integration, Socket.IO |

---

## Swagger / ReDoc

Interactive docs (includes admin routes — ignore admin-panel sections for the website):

- Swagger UI: `http://16.16.160.64:8000/swagger/`
- ReDoc: `http://16.16.160.64:8000/redoc/`

---

*Generated for Reachtolet website integration. Admin panel APIs (`/api/admin-panel/*`) and staff billboard approval endpoints are intentionally omitted.*
