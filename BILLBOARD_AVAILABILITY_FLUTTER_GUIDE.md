# Billboard Availability & API Changes — Flutter Implementation Guide

This guide is for the Flutter app developer. It documents **recent backend API changes**, with focus on the new **dedicated availability APIs** and what to stop using from the old update flow.

**Base URL:** `http://127.0.0.1:8000` (replace with production URL)

**Auth header (when required):**
```
Authorization: Bearer <access_token>
```

---

## Quick migration checklist

| # | Action | Priority |
|---|--------|----------|
| 1 | **Stop** sending `unavailable_dates` in `PUT/PATCH /api/billboards/{id}/` | Required |
| 2 | **Use** `PUT /api/billboards/{id}/availability/` to save calendar booked dates | Required |
| 3 | **Use** `GET /api/billboards/{id}/availability/` when opening the availability calendar | Required |
| 4 | Replace `unavailable_dates` reads with `availability.booked_dates` | Required |
| 5 | Map screen: use minimal list response (`id`, `latitude`, `longitude`, `count`) then fetch detail by id | Required |
| 6 | Most POST actions now return only `status_code` + `message` (auth endpoints still return tokens) | Required |

---

## 1. NEW: Dedicated availability APIs

Availability is no longer managed through the generic billboard update API.

### Terminology

| UI label | API field | Meaning |
|----------|-----------|---------|
| **Booked** (red dot on calendar) | `booked_dates` | Date is not available |
| **Available** (empty on calendar) | not in `booked_dates` | Date is open |

Dates are stored as strings: **`YYYY-MM-DD`** (example: `"2026-10-05"`).

---

### 1.1 Get availability (public)

Use when:
- Media owner opens **Set Availability** calendar
- Advertiser opens **Billboard Details** calendar

```bash
curl "http://127.0.0.1:8000/api/billboards/12/availability/"
```

**Optional month filter:**
```bash
curl "http://127.0.0.1:8000/api/billboards/12/availability/?from=2026-10-01&to=2026-10-31"
```

**Response `200`:**
```json
{
  "billboard_id": 12,
  "booked_dates": [
    "2026-10-05",
    "2026-10-06",
    "2026-10-12"
  ],
  "total_booked": 3
}
```

**With `from` / `to` query params:**
```json
{
  "billboard_id": 12,
  "from": "2026-10-01",
  "to": "2026-10-31",
  "booked_dates": [
    "2026-10-05",
    "2026-10-06",
    "2026-10-12"
  ],
  "total_booked": 3
}
```

**Response `404`:**
```json
{
  "status_code": 404,
  "message": "Billboard not found"
}
```

**Response `400` (bad date format):**
```json
{
  "status_code": 400,
  "message": "Invalid date format. Use YYYY-MM-DD."
}
```

**Flutter calendar logic:**
- Loop through days in visible month
- If `date` is in `booked_dates` → show **Booked** (red)
- Else → show **Available**

---

### 1.2 Set availability (media owner only)

Use when media owner taps **Save** on the availability calendar.

**Auth:** Required  
**Role:** `media_owner`  
**Ownership:** User must own the billboard

```bash
curl -X PUT "http://127.0.0.1:8000/api/billboards/12/availability/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "booked_dates": [
      "2026-10-05",
      "2026-10-06",
      "2026-10-12"
    ]
  }'
```

**Important:** Send the **full list** of booked dates after calendar editing (replace semantics, not patch).

**Clear all booked dates (all available):**
```json
{
  "booked_dates": []
}
```

**Response `200`:**
```json
{
  "status_code": 200,
  "message": "Availability updated successfully",
  "billboard_id": 12,
  "booked_dates": [
    "2026-10-05",
    "2026-10-06",
    "2026-10-12"
  ],
  "total_booked": 3
}
```

**Response `403`:**
```json
{
  "status_code": 403,
  "message": "You can only set availability for your own billboards."
}
```

**Response `400` (validation):**
```json
{
  "booked_dates": [
    "Invalid date format. Use YYYY-MM-DD."
  ]
}
```

---

### 1.3 Flutter flow: My OOH Media → Availability button

```
1. User taps "Availability" on billboard card (id = 12)
2. GET /api/billboards/12/availability/?from=<monthStart>&to=<monthEnd>
3. Render calendar with booked_dates as red
4. User toggles dates locally
5. On Save → PUT /api/billboards/12/availability/ with full booked_dates array
6. Use response.booked_dates to refresh UI
```

**Do NOT call:**
```
PUT /api/billboards/12/   ❌ (for availability)
```

---

## 2. BREAKING CHANGE: `unavailable_dates` removed

### Before (old — stop using)

```json
{
  "unavailable_dates": ["2026-10-05", "2026-10-06"]
}
```

Used in:
- `GET /api/billboards/{id}/`
- `PUT /api/billboards/{id}/`
- `GET /api/billboards/my-billboards/`
- Wishlist nested billboard object

### After (new)

**Read APIs** return:
```json
"availability": {
  "booked_dates": ["2026-10-05", "2026-10-06"],
  "total_booked": 2
}
```

**Write APIs** (`POST/PUT/PATCH` billboard) **ignore** these fields if sent:
- `unavailable_dates`
- `booked_dates`
- `availability`

They will **not** update the calendar.

---

## 3. Affected APIs — full list

### 3.1 `GET /api/billboards/` — public map/list (CHANGED)

**Before:** Returned full billboard objects (name, price, images, etc.)

**Now:** Returns **minimal markers only**. Fetch detail separately.

```bash
curl "http://127.0.0.1:8000/api/billboards/"
```

**Response `200` (paginated list):**
```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 150,
  "total_pages": 8,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "latitude": 40.7128,
      "longitude": -74.0060,
      "count": 1
    }
  ]
}
```

**Map bounds (no pagination):**
```bash
curl "http://127.0.0.1:8000/api/billboards/?ne_lat=41.0&ne_lng=-73.0&sw_lat=40.0&sw_lng=-75.0"
```

**Response `200`:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "latitude": 40.7128,
      "longitude": -74.0060,
      "count": 1
    }
  ],
  "clustering_enabled": false
}
```

**Clustered map:**
```bash
curl "http://127.0.0.1:8000/api/billboards/?ne_lat=41.0&ne_lng=-73.0&sw_lat=40.0&sw_lng=-75.0&cluster=true&zoom=8"
```

**Response `200`:**
```json
{
  "count": 150,
  "clustered_count": 12,
  "clusters": [
    {
      "type": "marker",
      "id": 1,
      "latitude": 40.7128,
      "longitude": -74.0060,
      "count": 1
    },
    {
      "type": "cluster",
      "id": null,
      "latitude": 40.8000,
      "longitude": -73.9500,
      "count": 25
    }
  ],
  "clustering_enabled": true,
  "zoom_level": 8.0
}
```

**Flutter change:**
- Map pins: use `id`, `latitude`, `longitude` only
- On marker/cluster tap → `GET /api/billboards/{id}/` for full detail

---

### 3.2 `GET /api/billboards/{id}/` — billboard detail (CHANGED)

**Before:** Had `unavailable_dates` array at root

**Now:** Has `availability` object. Full billboard fields unchanged otherwise.

```bash
curl "http://127.0.0.1:8000/api/billboards/12/"
```

**Response `200`:**
```json
{
  "id": 12,
  "city": "Lahore",
  "description": "Premium digital billboard",
  "number_of_boards": "2",
  "average_daily_views": "50000",
  "traffic_direction": "Northbound",
  "road_position": "Right side",
  "road_name": "Main Street",
  "exposure_time": "24/7",
  "price_range": "$500-$1000",
  "display_height": "10ft",
  "display_width": "20ft",
  "advertiser_phone": "+12025550123",
  "advertiser_whatsapp": "+12025550123",
  "company_name": "ACME Ads",
  "company_website": "https://acme.com",
  "ooh_media_type": "Digital",
  "ooh_media_id": "OOH-001",
  "type": "Roadside",
  "images": [
    "https://example.com/image1.jpg"
  ],
  "availability": {
    "booked_dates": [
      "2026-10-05",
      "2026-10-06",
      "2026-10-12"
    ],
    "total_booked": 3
  },
  "latitude": 31.5204,
  "longitude": 74.3587,
  "views": 120,
  "leads": 15,
  "is_active": true,
  "address": "123 Main Street, Lahore",
  "generator_backup": "Yes",
  "created_at": "2026-04-12T17:45:47.707825Z",
  "user_name": "John Doe",
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-04-13T10:00:00Z",
  "rejected_at": null,
  "rejection_reason": null,
  "approved_by_username": null,
  "rejected_by_username": null,
  "is_in_wishlist": false
}
```

**Flutter change:**
- Replace `billboard.unavailable_dates` → `billboard.availability.booked_dates`
- Detail calendar can use this object OR call dedicated availability GET

---

### 3.3 `PUT /api/billboards/{id}/` — edit billboard (CHANGED)

**Before:** Could send `unavailable_dates` to update calendar

**Now:** Availability fields are **stripped/ignored**. Use only for billboard profile fields (city, price, images, etc.)

```bash
curl -X PUT "http://127.0.0.1:8000/api/billboards/12/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Lahore",
    "description": "Updated description",
    "ooh_media_type": "Digital",
    "type": "Roadside",
    "price_range": "$500-$1000",
    "images": ["https://example.com/image1.jpg"]
  }'
```

**Response `200`:** Full billboard object (same shape as GET detail, with `availability` object).

**Flutter change:**
- Remove `unavailable_dates` from edit billboard payload
- Availability button must call `PUT /api/billboards/{id}/availability/`

---

### 3.4 `POST /api/billboards/` — create billboard (CHANGED)

**Before:** Could include `unavailable_dates` on create

**Now:** Availability fields ignored on create. New billboards start with empty `booked_dates`.

```bash
curl -X POST "http://127.0.0.1:8000/api/billboards/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Lahore",
    "description": "New billboard",
    "ooh_media_type": "Digital",
    "type": "Roadside",
    "latitude": 31.5204,
    "longitude": 74.3587
  }'
```

**Response `201`:**
```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

**Flutter change:**
- After create, if owner wants dates → open availability screen → `PUT /availability/`

---

### 3.5 `GET /api/billboards/my-billboards/` — owner list (CHANGED)

**Before:** Each item had `unavailable_dates`

**Now:** Each item has `availability` object (same as detail).

```bash
curl "http://127.0.0.1:8000/api/billboards/my-billboards/" \
  -H "Authorization: Bearer <access_token>"
```

**Response `200`:**
```json
{
  "links": { "next": null, "previous": null },
  "count": 4,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 12,
      "city": "Lahore",
      "description": "Oh2",
      "number_of_boards": "146",
      "average_daily_views": null,
      "traffic_direction": null,
      "road_position": null,
      "road_name": "Oh2",
      "exposure_time": null,
      "price_range": null,
      "display_height": null,
      "display_width": null,
      "advertiser_phone": null,
      "advertiser_whatsapp": null,
      "company_name": null,
      "company_website": null,
      "ooh_media_type": "Digital",
      "ooh_media_id": null,
      "type": "Lighting",
      "images": [],
      "availability": {
        "booked_dates": ["2026-10-05"],
        "total_booked": 1
      },
      "latitude": 31.52,
      "longitude": 74.35,
      "views": 2,
      "leads": 0,
      "is_active": true,
      "address": null,
      "generator_backup": null,
      "created_at": "2026-04-12T17:45:47.707825Z",
      "user_name": null,
      "approval_status": "approved",
      "approval_status_display": "Approved",
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

### 3.6 `GET /api/billboards/wishlist/` — wishlist (CHANGED)

Nested `billboard` object now uses `availability` instead of `unavailable_dates`.

```bash
curl "http://127.0.0.1:8000/api/billboards/wishlist/" \
  -H "Authorization: Bearer <access_token>"
```

**Response `200` (each result):**
```json
{
  "id": 1,
  "billboard": {
    "id": 12,
    "city": "Lahore",
    "...": "...",
    "availability": {
      "booked_dates": ["2026-10-05"],
      "total_booked": 1
    },
    "is_in_wishlist": true
  },
  "created_at": "2026-05-01T12:00:00Z"
}
```

---

## 4. POST response pattern (most action endpoints)

Most non-auth POST/PUT action endpoints now return:

```json
{
  "status_code": 200,
  "message": "Action completed successfully"
}
```

### Auth endpoints still return JWT tokens

These are **exceptions** — Flutter must still read `access` and `refresh`:

| Endpoint | Returns tokens? |
|----------|-----------------|
| `POST /api/users/login/` | Yes |
| `POST /api/users/register/` | Yes |
| `POST /api/users/token/refresh/` | Yes |
| `POST /api/users/google-login/` | Yes |

**Login response `200`:**
```json
{
  "status_code": 200,
  "message": "Logged in successfully",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "user_type": "advertiser"
  }
}
```

**Register response `201`:**
```json
{
  "status_code": 201,
  "message": "User registered successfully",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone": "+12025550123",
    "country_code": "US",
    "user_type": "advertiser"
  }
}
```

**Refresh response `200`:**
```json
{
  "status_code": 200,
  "message": "Token refreshed successfully",
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Other POST examples (minimal response)

**Track view:**
```bash
curl -X POST "http://127.0.0.1:8000/api/billboards/12/track-view/"
```
```json
{
  "status_code": 200,
  "message": "View tracked successfully"
}
```

**Track lead:**
```json
{
  "status_code": 200,
  "message": "Lead tracked successfully"
}
```

**Wishlist toggle:**
```json
{
  "status_code": 201,
  "message": "Added to wishlist"
}
```

**Logout:**
```json
{
  "status_code": 200,
  "message": "Logged out successfully"
}
```

---

## 5. Suggested Dart model changes

### Old model (remove)
```dart
// ❌ Remove from Billboard model
List<String>? unavailableDates;
```

### New model (add)
```dart
class BillboardAvailability {
  final List<String> bookedDates;
  final int totalBooked;

  BillboardAvailability({
    required this.bookedDates,
    required this.totalBooked,
  });

  factory BillboardAvailability.fromJson(Map<String, dynamic> json) {
    return BillboardAvailability(
      bookedDates: List<String>.from(json['booked_dates'] ?? []),
      totalBooked: json['total_booked'] ?? 0,
    );
  }
}

class Billboard {
  final int id;
  final BillboardAvailability? availability;
  // ... other fields

  factory Billboard.fromJson(Map<String, dynamic> json) {
    return Billboard(
      id: json['id'],
      availability: json['availability'] != null
          ? BillboardAvailability.fromJson(json['availability'])
          : null,
      // ...
    );
  }
}
```

### Map list item (minimal)
```dart
class BillboardMarker {
  final int id;
  final double? latitude;
  final double? longitude;
  final int count;

  factory BillboardMarker.fromJson(Map<String, dynamic> json) {
    return BillboardMarker(
      id: json['id'],
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      count: json['count'] ?? 1,
    );
  }
}
```

---

## 6. Suggested API service methods

```dart
// Availability
Future<AvailabilityResponse> getBillboardAvailability(
  int billboardId, {
  String? from,
  String? to,
}) async {
  final query = <String, String>{};
  if (from != null) query['from'] = from;
  if (to != null) query['to'] = to;

  final response = await dio.get(
    '/api/billboards/$billboardId/availability/',
    queryParameters: query.isEmpty ? null : query,
  );
  return AvailabilityResponse.fromJson(response.data);
}

Future<AvailabilityUpdateResponse> setBillboardAvailability(
  int billboardId,
  List<String> bookedDates,
) async {
  final response = await dio.put(
    '/api/billboards/$billboardId/availability/',
    data: {'booked_dates': bookedDates},
  );
  return AvailabilityUpdateResponse.fromJson(response.data);
}

// Map
Future<List<BillboardMarker>> getBillboardMarkers({...bounds}) async {
  final response = await dio.get('/api/billboards/', queryParameters: {...});
  return (response.data['results'] as List)
      .map((e) => BillboardMarker.fromJson(e))
      .toList();
}

// Detail (full data + availability)
Future<Billboard> getBillboardDetail(int id) async {
  final response = await dio.get('/api/billboards/$id/');
  return Billboard.fromJson(response.data);
}
```

---

## 7. Screen-by-screen changes

| Screen | Old behavior | New behavior |
|--------|--------------|--------------|
| **Map** | Parsed full billboard from list API | Parse minimal markers; fetch detail on tap |
| **Billboard Details** | `unavailable_dates` for calendar | `availability.booked_dates` or GET availability |
| **My OOH Media → Availability** | `PUT /billboards/{id}/` with dates | `GET` then `PUT /billboards/{id}/availability/` |
| **Edit Billboard** | Could include dates in same form | Dates removed from edit payload |
| **Create Billboard** | Could set dates on create | Set dates separately via availability API |
| **Wishlist** | `billboard.unavailable_dates` | `billboard.availability.booked_dates` |

---

## 8. Error handling tips

1. Check `status_code` in JSON body **and** HTTP status code.
2. Validation errors on availability PUT may still use DRF field format:
   ```json
   {
     "booked_dates": ["Invalid date format. Use YYYY-MM-DD."]
   }
   ```
3. `403` on availability PUT → user is not media owner or does not own billboard.
4. After availability save, prefer `response.booked_dates` from PUT response to refresh calendar immediately.

---

## 9. Summary: what to delete vs add in Flutter

### Delete / stop using
- `unavailable_dates` field in models and API calls
- Sending dates in `PUT /api/billboards/{id}/`
- Sending dates in `POST /api/billboards/`
- Expecting full billboard objects from `GET /api/billboards/` list/map
- Expecting rich data from most POST responses (except auth)

### Add / start using
- `GET /api/billboards/{id}/availability/`
- `PUT /api/billboards/{id}/availability/`
- `availability.booked_dates` on read APIs
- `GET /api/billboards/{id}/` after map marker tap
- Minimal marker model for map list endpoint

---

## 10. Endpoint reference (new + changed only)

| Method | Endpoint | Auth | Change |
|--------|----------|------|--------|
| **GET** | `/api/billboards/{id}/availability/` | Public | **NEW** |
| **PUT** | `/api/billboards/{id}/availability/` | Owner | **NEW** |
| GET | `/api/billboards/` | Public | Minimal markers only |
| GET | `/api/billboards/{id}/` | Public | `availability` replaces `unavailable_dates` |
| PUT | `/api/billboards/{id}/` | Owner | Ignores availability fields |
| POST | `/api/billboards/` | Owner | Ignores availability fields; minimal response |
| GET | `/api/billboards/my-billboards/` | Owner | `availability` object |
| GET | `/api/billboards/wishlist/` | User | Nested `availability` object |

---

**Questions?** Test against Swagger: `http://127.0.0.1:8000/swagger/`
