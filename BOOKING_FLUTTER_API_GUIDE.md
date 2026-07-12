# Booking System — Flutter Implementation Guide

Complete API reference for the Reachtolet **bookings** feature (hotel-style date ranges + media-type creative).

**Base URL:** `http://16.16.160.64:8000`  
**Auth:** `Authorization: Bearer <access>` (unless noted Public)

After deploy:

```bash
python manage.py migrate
# restart Daphne
```

---

## 1. Concepts (read once)

### Two layers

| Layer | Table | When |
|-------|--------|------|
| Inventory | `Booking` | Dates + accept/reject |
| Creative | `BookingContent` | **Only after** owner accepts |
| Money | `Payment` | V1 always `skipped` |

### Booking statuses

| Status | Meaning |
|--------|---------|
| `pending` | Waiting on media owner (soft-holds calendar) |
| `accepted` | Owner said yes — advertiser submits content |
| `paid` | Reserved for V2 payment (unused in V1) |
| `confirmed` | Content approved; flight not started yet |
| `live` | Today is inside start→end |
| `completed` | End date passed |
| `rejected` | Owner rejected request |
| `cancelled` | Cancelled / pending expired (48h) |

### Content statuses

| Status | Meaning |
|--------|---------|
| `awaiting_input` | Accepted; waiting for advertiser |
| `submitted` | Waiting for owner review |
| `owner_approved` | Creative OK → booking becomes confirmed/live |
| `owner_rejected` | Advertiser may resubmit |

### Content types

Derived from billboard media type:

- `digital` — upload file / `video_url` + optional daypart/duration  
- `static` — `install_notes` required (no vinyl upload)

Media-types list now also returns:

```json
{
  "content_type": "digital",
  "allows_in_app_media": true,
  "requires_slot_timing": true,
  "creative_hint": "Upload MP4/JPG..."
}
```

---

## 2. Flutter flow (both roles)

```
Advertiser                         Media owner
─────────                          ───────────
GET calendar (busy)                
POST /bookings/  → pending  ──►    GET /bookings/?role=owner
                                   POST .../accept/  or  .../reject/
← accepted + content awaiting      
POST .../content/ (digital/static) 
                                   POST .../content/approve/
← confirmed / live                 
```

---

## 3. Endpoints

### 3.1 Calendar (guest OK)

`GET /api/billboards/{billboard_id}/calendar/?from=YYYY-MM-DD&to=YYYY-MM-DD`

```bash
curl -s "http://16.16.160.64:8000/api/billboards/101/calendar/?from=2026-08-01&to=2026-08-31"
```

**200**
```json
{
  "status_code": 200,
  "message": "Calendar retrieved successfully",
  "billboard_id": 101,
  "from": "2026-08-01",
  "to": "2026-08-31",
  "busy": [
    {
      "start": "2026-08-05",
      "end": "2026-08-12",
      "reason": "booked",
      "booking_id": 3,
      "status": "confirmed"
    },
    {
      "start": "2026-08-20",
      "end": "2026-08-20",
      "reason": "owner_block",
      "booking_id": null,
      "status": null
    },
    {
      "start": "2026-08-15",
      "end": "2026-08-17",
      "reason": "pending_hold",
      "booking_id": 9,
      "status": "pending"
    }
  ],
  "content_capabilities": {
    "content_type": "digital",
    "allows_in_app_media": true,
    "requires_slot_timing": true,
    "creative_hint": "Upload MP4/JPG and optionally set daypart / duration."
  }
}
```

`reason`: `booked` | `pending_hold` | `owner_block`  
Paint calendar: free = not covered by any busy range.

**400** `{ "status_code": 400, "message": "Invalid date format. Use YYYY-MM-DD." }`

---

### 3.2 Create booking request (advertiser)

`POST /api/bookings/`

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/" \
  -H "Authorization: Bearer ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "billboard_id": 101,
    "start_date": "2026-09-01",
    "end_date": "2026-09-14",
    "message": "Product launch campaign"
  }'
```

**201**
```json
{
  "status_code": 201,
  "message": "Booking request created successfully",
  "booking": { /* Booking object — see §4 */ }
}
```

**Errors**

| Code | message (examples) |
|------|--------------------|
| 403 | Only advertisers can request bookings. |
| 404 | Billboard not found. |
| 400 | end_date must be on or after start_date. / start_date cannot be in the past. / This billboard is not available for booking. |
| 409 | Selected dates overlap an existing booking or hold. |

---

### 3.3 List my bookings (paginated)

`GET /api/bookings/?page=1&page_size=20&role=advertiser|owner&status=pending`

```bash
curl -s "http://16.16.160.64:8000/api/bookings/?role=owner&status=pending&page=1&page_size=20" \
  -H "Authorization: Bearer ACCESS"
```

**200**
```json
{
  "links": { "next": null, "previous": null },
  "count": 2,
  "total_pages": 1,
  "current_page": 1,
  "results": [ /* Booking objects */ ],
  "status_code": 200,
  "message": "Bookings retrieved successfully"
}
```

- Default role: inferred from `user_type` if `role` omitted  
- `status` optional filter  

---

### 3.4 Booking detail

`GET /api/bookings/{id}/`

```bash
curl -s "http://16.16.160.64:8000/api/bookings/12/" \
  -H "Authorization: Bearer ACCESS"
```

**200**
```json
{
  "status_code": 200,
  "message": "Booking retrieved successfully",
  "booking": { /* Booking object */ }
}
```

**403** not a participant · **404** not found

---

### 3.5 Accept (media owner)

`POST /api/bookings/{id}/accept/`

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/accept/" \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"owner_note": "Looks good — send creative by Friday"}'
```

**200**
```json
{
  "status_code": 200,
  "message": "Booking accepted successfully",
  "booking": {
    "status": "accepted",
    "content": {
      "content_type": "digital",
      "status": "awaiting_input",
      "...": "..."
    },
    "payment": { "status": "skipped" }
  }
}
```

Creates empty `BookingContent` (`awaiting_input`).  
**409** if dates no longer free.

---

### 3.6 Reject (media owner)

`POST /api/bookings/{id}/reject/`

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/reject/" \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Board reserved for another campaign"}'
```

**200** `{ "status_code": 200, "message": "Booking rejected successfully", "booking": { "status": "rejected", ... } }`

---

### 3.7 Cancel (advertiser or owner)

`POST /api/bookings/{id}/cancel/`

Allowed when status is `pending`, `accepted`, or `paid`.

**200** `{ "status_code": 200, "message": "Booking cancelled successfully", "booking": { "status": "cancelled", ... } }`

---

### 3.8 Submit content (advertiser) — after accepted

`POST /api/bookings/{id}/content/`  
`Content-Type: multipart/form-data` **or** JSON

#### Digital

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/content/" \
  -H "Authorization: Bearer ADV_ACCESS" \
  -F "media_file=@/path/ad.mp4" \
  -F "slot_daypart=evening" \
  -F "duration_seconds=15" \
  -F "digital_notes=Loop every 3 minutes"
```

Or JSON with URL:

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/content/" \
  -H "Authorization: Bearer ADV_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://cdn.example.com/ad.mp4",
    "slot_daypart": "morning",
    "duration_seconds": 10,
    "digital_notes": "Prefer 8–10am"
  }'
```

Requires **file or `video_url`**.

#### Static

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/content/" \
  -H "Authorization: Bearer ADV_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "install_notes": "Vinyl 12x6ft, deliver to site by Aug 28. Printer: XYZ Prints.",
    "external_link": "https://drive.google.com/..."
  }'
```

Requires **`install_notes`**.

**200** `{ "status_code": 200, "message": "Content submitted successfully", "booking": { "content": { "status": "submitted", ... } } }`

---

### 3.9 Approve content (owner)

`POST /api/bookings/{id}/content/approve/`

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/content/approve/" \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"install_confirmed": true}'
```

`install_confirmed` only relevant for static (owner ticks install plan).

**200**
```json
{
  "status_code": 200,
  "message": "Content approved; booking confirmed",
  "booking": {
    "status": "confirmed",
    "content": { "status": "owner_approved" },
    "payment": { "status": "skipped" }
  }
}
```

If `start_date <= today <= end_date` → status becomes **`live`** instead of `confirmed`.

---

### 3.10 Reject content (owner)

`POST /api/bookings/{id}/content/reject/`

```bash
curl -s -X POST "http://16.16.160.64:8000/api/bookings/12/content/reject/" \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Video too dark — please re-export"}'
```

**200** content status → `owner_rejected`; advertiser may POST content again.

---

## 4. Booking object shape

```json
{
  "id": 12,
  "billboard_id": 101,
  "billboard": {
    "id": 101,
    "city": "Lahore",
    "road_name": "MM Alam",
    "ooh_media_type": "Digital Billboard",
    "currency": "PKR",
    "image": "https://...",
    "content_capabilities": {
      "content_type": "digital",
      "allows_in_app_media": true,
      "requires_slot_timing": true,
      "creative_hint": "..."
    }
  },
  "advertiser_id": 9,
  "advertiser": {
    "id": 9,
    "email": "adv@example.com",
    "full_name": "Sara Adv",
    "user_type": "advertiser"
  },
  "media_owner_id": 12,
  "media_owner": {
    "id": 12,
    "email": "owner@example.com",
    "full_name": "Ali Owner",
    "user_type": "media_owner"
  },
  "start_date": "2026-09-01",
  "end_date": "2026-09-14",
  "status": "accepted",
  "status_display": "Accepted",
  "total_price": "50000.00",
  "currency": "PKR",
  "advertiser_message": "Product launch",
  "rejection_reason": "",
  "owner_note": "Send creative by Friday",
  "expires_at": null,
  "content": {
    "id": 1,
    "content_type": "digital",
    "status": "awaiting_input",
    "video_url": "",
    "media_file_url": null,
    "slot_daypart": "",
    "duration_seconds": null,
    "digital_notes": "",
    "install_notes": "",
    "install_confirmed_by_owner": false,
    "external_link": "",
    "owner_feedback": "",
    "submitted_at": null,
    "reviewed_at": null,
    "created_at": "...",
    "updated_at": "..."
  },
  "payment": {
    "id": 1,
    "amount": "50000.00",
    "currency": "PKR",
    "status": "skipped",
    "gateway_ref": "",
    "created_at": "...",
    "updated_at": "..."
  },
  "created_at": "...",
  "updated_at": "..."
}
```

Before accept, `content` is `null`.

---

## 5. Error envelope (bookings)

```json
{ "status_code": 400, "message": "Human readable error" }
```

Also standard DRF validation:

```json
{ "start_date": ["Date has wrong format."] }
```

| HTTP | When |
|------|------|
| 200 | Success mutations / detail |
| 201 | Create booking |
| 400 | Validation / wrong status |
| 401 | Missing/invalid JWT |
| 403 | Wrong role |
| 404 | Not found |
| 409 | Date overlap conflict |

---

## 6. Inbox notification types (booking)

| `notification_type` | To | When |
|---------------------|-----|------|
| `booking_requested` | Owner | New request |
| `booking_accepted` | Advertiser | Accept |
| `booking_rejected` | Advertiser | Reject |
| `booking_content_submitted` | Owner | Content submitted |
| `booking_content_rejected` | Advertiser | Content rejected |
| `booking_confirmed` | Both | Content approved |

`data` includes: `booking_id`, `billboard_id`, `status`, `start_date`, `end_date`.

Use existing inbox APIs under `/api/notifications/inbox/`.

---

## 7. Suggested Flutter screens

| Screen | Role | APIs |
|--------|------|------|
| Board detail calendar | Both / guest | `GET .../calendar/` |
| Request booking sheet | Advertiser | `POST /bookings/` |
| My requests | Advertiser | `GET /bookings/?role=advertiser` |
| Incoming requests | Owner | `GET /bookings/?role=owner&status=pending` |
| Booking detail | Both | `GET /bookings/{id}/` |
| Accept / Reject | Owner | `.../accept/` `.../reject/` |
| Submit creative | Advertiser | Branch UI on `content.content_type` → `POST .../content/` |
| Review creative | Owner | `.../content/approve/` `.../content/reject/` |

### UI branch (critical)

```dart
final caps = booking.billboard.contentCapabilities;
// or booking.content?.contentType
if (caps.contentType == 'digital') {
  // file picker + daypart + duration
} else {
  // install_notes + optional external_link — NO file required
}
```

---

## 8. AppUrls to add

```dart
static String billboardCalendar(int id) =>
    '$baseUrl/api/billboards/$id/calendar/';
static const String bookings = '$baseUrl/api/bookings/';
static String bookingDetail(int id) => '$baseUrl/api/bookings/$id/';
static String bookingAccept(int id) => '$baseUrl/api/bookings/$id/accept/';
static String bookingReject(int id) => '$baseUrl/api/bookings/$id/reject/';
static String bookingCancel(int id) => '$baseUrl/api/bookings/$id/cancel/';
static String bookingContent(int id) => '$baseUrl/api/bookings/$id/content/';
static String bookingContentApprove(int id) =>
    '$baseUrl/api/bookings/$id/content/approve/';
static String bookingContentReject(int id) =>
    '$baseUrl/api/bookings/$id/content/reject/';
```

---

## 9. V1 vs later payment

V1: `payment.status` is always **`skipped`**. After content approve → `confirmed`/`live` (no `paid` step).

V2 (JazzCash / Easypaisa): insert charge **on accept** → status `paid` → then content → `confirmed`. Architecture already has `Payment` + `paid` status.

---

## 10. Checklist

- [ ] Migrate: `bookings.0001`, `notifications.0005`
- [ ] Guest can load calendar without JWT
- [ ] Advertiser request → owner sees pending (paginated)
- [ ] Overlap returns **409**
- [ ] Accept creates `content` with correct `content_type`
- [ ] Digital requires file or URL; static requires install_notes
- [ ] Approve → confirmed/live; inbox fires
- [ ] Reject content allows resubmit
- [ ] Pending expires after 48h (advanced on list/detail)

---

**Backend app:** `bookings`  
**Mount:** `/api/bookings/` + `/api/billboards/{id}/calendar/`
