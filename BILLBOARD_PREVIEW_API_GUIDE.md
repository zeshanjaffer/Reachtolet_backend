# Billboard Preview API Guide

Lightweight endpoint for the **map pin preview dialog** before the full detail screen.

---

## API flow (3 steps)

| Step | Screen | Endpoint |
|------|--------|----------|
| 1 | Map with pins | `GET /api/billboards/` |
| 2 | Preview bottom sheet | **`GET /api/billboards/{id}/preview/`** |
| 3 | Full detail page | `GET /api/billboards/{id}/` |

Optional calendar: `GET /api/billboards/{id}/availability/`

---

## Preview endpoint

```
GET /api/billboards/{id}/preview/
Authorization: Bearer {access_token}
```

**Who can access:**
- Any authenticated user (advertiser or media owner) for **approved + active** billboards
- Media owners can also preview **their own** billboards (any status)

---

## Example curl

```bash
BASE_URL="http://16.16.160.64:8000"
ACCESS="YOUR_ACCESS_TOKEN"

curl --location "$BASE_URL/api/billboards/20/preview/" \
  --header "Authorization: Bearer $ACCESS"
```

---

## Success response — HTTP 200

```json
{
  "id": 20,
  "city": "Lahore",
  "road_name": "Jailroad",
  "image": "https://16.16.160.64:8000/media/billboards/example.jpg",
  "price": {
    "amount": "2000000",
    "currency": "PKR",
    "period": "per month"
  },
  "display_size": {
    "width": "50",
    "height": "60",
    "unit": "meters",
    "label": "50 × 60 meters"
  },
  "views_per_day": "124",
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

---

## Field reference

| Field | Source | Notes |
|-------|--------|-------|
| `image` | First URL in `images[]` | `null` if no images |
| `price.amount` | `price_range` | String as stored in DB |
| `price.period` | `exposure_time` | Defaults to `"per month"` |
| `price.currency` | Fixed | `"PKR"` |
| `display_size.label` | `display_width` × `display_height` | `null` if dimensions missing |
| `views_per_day` | `average_daily_views` | Can be `null` |
| `availability.status` | Computed | `available`, `booked`, or `inactive` |
| `availability.total_booked` | Count of booked dates | |
| `lighting.has_lighting` | `generator_backup == "Yes"` | |
| `is_in_wishlist` | Wishlist check | For logged-in user |

### Availability status logic

| Status | Condition |
|--------|-----------|
| `inactive` | `is_active == false` |
| `booked` | Today is in `booked_dates` |
| `available` | Otherwise |

---

## Errors

| HTTP | Body |
|------|------|
| 401 | `{"detail":"Authentication credentials were not provided."}` |
| 404 | `{"detail":"Not found."}` |

---

## Flutter implementation

### 1. Map screen — load pins

```dart
final response = await api.get('/api/billboards/?page_size=100');
// results: [{ id, latitude, longitude, count }]
```

### 2. Pin tapped — show preview sheet

```dart
final preview = await api.get('/api/billboards/$id/preview/');
// Use: image, price, views_per_day, availability.label, display_size.label
```

### 3. "View details" — full screen

```dart
final detail = await api.get('/api/billboards/$id/');
// Full billboard object with all fields
```

### Preview vs detail

| Preview | Detail |
|---------|--------|
| 1 image | All images |
| Price summary | Full pricing + company info |
| Availability badge | Full `availability.booked_dates` |
| No phone / description | Full contact + description |

---

## Postman

1. **Method:** GET  
2. **URL:** `{{base_url}}/api/billboards/20/preview/`  
3. **Auth:** Bearer `{{access_token}}`

---

## Files changed

- `billboards/serializers.py` — `BillboardPreviewSerializer`
- `billboards/views.py` — `BillboardPreviewView`
- `billboards/urls.py` — route registration
- `billboards/availability_utils.py` — `get_availability_status()`
