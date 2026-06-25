# Billboard Map → Preview → Detail API Guide

3-step flow for the **advertiser map** (Flutter / Next.js).

**Base URL:** `http://16.16.160.64:8000`  
**Auth:** All 3 endpoints require `Authorization: Bearer {access_token}`

---

## Screen flow

```
┌─────────────────┐     tap pin      ┌──────────────────┐    "View detail"    ┌─────────────────┐
│  1. MAP         │  ──────────────► │  2. PREVIEW      │  ─────────────────► │  3. DETAIL      │
│  GET /billboards│                  │  GET .../preview/│                     │  GET .../{id}/  │
│  id, lat, lng   │                  │  card summary    │                     │  full page      │
└─────────────────┘                  └──────────────────┘                     └─────────────────┘
```

---

## API 1 — Public map list (pins on map)

**When:** Map loads / user drags map (send current viewport bounds).

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/` |

### Query params (map mode)

| Param | Required | Example |
|---|---|---|
| `ne_lat` | Yes (map) | `32` |
| `ne_lng` | Yes (map) | `75` |
| `sw_lat` | Yes (map) | `31` |
| `sw_lng` | Yes (map) | `74` |
| `cluster` | Optional | `true` |
| `zoom` | Optional | `12` |

### curl

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ne_lat=32&ne_lng=75&sw_lat=31&sw_lng=74&cluster=true&zoom=12" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 200 OK — markers (no clustering)

```json
{
  "count": 3,
  "results": [
    {
      "id": 45,
      "latitude": 31.5160599886659,
      "longitude": 74.3428447310015,
      "count": 1
    },
    {
      "id": 44,
      "latitude": 31.471599,
      "longitude": 74.260792,
      "count": 1
    },
    {
      "id": 42,
      "latitude": 31.5204,
      "longitude": 74.3587,
      "count": 1
    }
  ],
  "clustering_enabled": false
}
```

Each item = one pin. Use **`id`** for the next API.  
`count` is always `1` per marker.

### 200 OK — clustered (many pins)

```json
{
  "count": 50,
  "clustered_count": 8,
  "clusters": [
    {
      "type": "cluster",
      "cluster_id": 12,
      "latitude": 31.48,
      "longitude": 74.30,
      "count": 5,
      "expansion_zoom": 14
    },
    {
      "type": "marker",
      "id": 44,
      "latitude": 31.471599,
      "longitude": 74.260792,
      "count": 1
    }
  ],
  "clustering_enabled": true,
  "zoom_level": 12.0
}
```

| `type` | Action |
|---|---|
| `marker` | Use `id` → call preview API |
| `cluster` | Zoom map to `expansion_zoom` |

### Other status codes

| HTTP | Response |
|---|---|
| **401** | `{"detail": "Authentication credentials were not provided."}` |
| **200** (empty) | `{"count": 0, "results": [], "clustering_enabled": false}` |

---

## API 2 — Preview (tap pin → bottom sheet / card)

**When:** User taps a map pin. Lightweight data for a quick card before full page.

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/{id}/preview/` |

Replace `{id}` with pin `id` from API 1 (e.g. `44`).

### curl

```bash
curl --location "http://16.16.160.64:8000/api/billboards/44/preview/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 200 OK — example (`laore` billboard)

```json
{
  "id": 44,
  "city": "laore",
  "road_name": "as",
  "image": "http://16.16.160.64:8000/media/billboards/bd74f0c279af4d3d90014570c00d62b4.png",
  "price": {
    "amount": "899",
    "currency": "PKR",
    "period": "23 sec"
  },
  "display_size": {
    "width": "19",
    "height": "12",
    "unit": "meters",
    "label": "19 × 12 meters"
  },
  "views_per_day": "1234",
  "availability": {
    "status": "available",
    "label": "Available",
    "total_booked": 0
  },
  "lighting": {
    "has_lighting": true,
    "label": "Lighting"
  },
  "is_in_wishlist": false
}
```

### Field guide (preview card UI)

| Field | Use on UI |
|---|---|
| `city` | Title |
| `road_name` | Subtitle |
| `image` | Hero photo (first image) |
| `price.amount` + `price.currency` + `price.period` | Price line |
| `display_size.label` | Size text |
| `availability.label` | Green/red availability chip |
| `lighting.label` | Lighting badge |
| `is_in_wishlist` | Heart icon state |

### Other status codes

| HTTP | Response |
|---|---|
| **401** | `{"detail": "Authentication credentials were not provided."}` |
| **404** | Billboard not found or not visible |

---

## API 3 — Full detail (tap "View detail" → next screen)

**When:** User opens the full billboard page from preview.

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/billboards/{id}/` |

Same `{id}` as preview (e.g. `44`).

### curl

```bash
curl --location "http://16.16.160.64:8000/api/billboards/44/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 200 OK — full detail (example)

```json
{
  "id": 44,
  "city": "laore",
  "description": "askldnakl",
  "number_of_boards": "33",
  "average_daily_views": "1234",
  "traffic_direction": "ass",
  "road_position": "akls",
  "road_name": "as",
  "exposure_time": "23 sec",
  "price_range": "899",
  "display_height": "12",
  "display_width": "19",
  "advertiser_phone": "+923021245676",
  "advertiser_whatsapp": "+923021245676",
  "company_name": "asdkamd",
  "company_website": "asdad.com",
  "ooh_media_type": "Digital Billboard",
  "ooh_media_id": null,
  "type": "Premium",
  "images": [
    "http://16.16.160.64:8000/media/billboards/bd74f0c279af4d3d90014570c00d62b4.png"
  ],
  "specifications": {
    "slots": [],
    "currency": "PKR",
    "price_per_second": 899,
    "allowed_video_lengths": [10, 20, 30],
    "loop_duration_seconds": 60
  },
  "availability": {
    "booked_dates": [],
    "total_booked": 0
  },
  "latitude": 31.471599,
  "longitude": 74.260792,
  "views": 1,
  "leads": 0,
  "is_active": true,
  "address": "jaskdnsjkcn",
  "generator_backup": "Yes",
  "created_at": "2026-06-20T11:29:00.075736Z",
  "user_name": null,
  "approval_status": "approved",
  "approval_status_display": "Approved",
  "approved_at": "2026-06-20T11:29:00.075171Z",
  "rejected_at": null,
  "rejection_reason": null,
  "is_in_wishlist": false
}
```

### Extra fields on detail (not in preview)

| Field | Use on detail screen |
|---|---|
| `description` | About text |
| `images[]` | Image gallery / carousel |
| `specifications` | Digital slots, pricing JSON |
| `advertiser_phone` / `advertiser_whatsapp` | Call / WhatsApp buttons |
| `company_name` / `company_website` | Owner info |
| `address` | Full address |
| `latitude` / `longitude` | Mini-map |
| `views` / `leads` | Stats |
| `ooh_media_type` | Digital vs Static badge |

### Other status codes

| HTTP | Response |
|---|---|
| **401** | `{"detail": "Authentication credentials were not provided."}` |
| **404** | Billboard not found |

---

## Optional — track view when detail opens

```bash
curl --location --request POST "http://16.16.160.64:8000/api/billboards/44/track-view/" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "status_code": 200,
  "message": "View tracked successfully"
}
```

---

## Quick reference

| Step | Endpoint | Returns |
|---|---|---|
| 1 Map | `GET /api/billboards/?ne_lat&ne_lng&sw_lat&sw_lng` | `id`, `latitude`, `longitude`, `count` |
| 2 Preview | `GET /api/billboards/{id}/preview/` | Card: image, price, size, availability |
| 3 Detail | `GET /api/billboards/{id}/` | Everything for full page |

---

## Flutter pseudo-code

```dart
// 1. Map move
final map = await get('/api/billboards/?ne_lat=$ne&ne_lng=$neLng&sw_lat=$sw&sw_lng=$swLng&cluster=true&zoom=$zoom');

// 2. Pin tap
final preview = await get('/api/billboards/$id/preview/');
showBottomSheet(preview);

// 3. View detail button
final detail = await get('/api/billboards/$id/');
navigateTo(DetailScreen(detail));
```
