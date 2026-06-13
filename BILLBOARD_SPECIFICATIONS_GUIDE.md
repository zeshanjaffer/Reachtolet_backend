# Billboard Specifications API Guide

Flexible **`specifications`** JSON field for type-specific billboard data (digital slots, static pricing, etc.) sent from Flutter on create/update and returned on detail/list APIs.

**Base URL:** `http://16.16.160.64:8000`

---

## Task summary

### Problem (before)

Billboards share one flat database model (`city`, `price_range`, `exposure_time`, …). **Digital** and **Static** boards need very different extra data:

| Digital Billboard | Static Billboard |
|---|---|
| Loop duration (e.g. 60 sec) | Price per month |
| Allowed video lengths (10, 20, 30 sec) | Printing cost |
| Slot timeline (open / booked) | — |

There was **no place** to store this without adding many nullable columns or new tables for every media type.

### Solution (after)

Add one JSON column on `billboards_billboard`:

```
specifications  JSON  default {}
```

- **Create / update:** frontend sends `specifications` as a JSON string in `multipart/form-data`.
- **Read:** `GET /api/billboards/{id}/`, `GET /api/billboards/my-billboards/`, etc. return `specifications` as-is.
- **Media type:** use existing **`ooh_media_type`** (`"Digital Billboard"`, `"Static Billboard"`) — **no** separate `billboard_kind` field.
- **Validation:** backend only checks that `specifications` is a valid JSON **object** and under 20 KB. **Frontend is free** to send any keys per media type.

### Files changed

| File | Change |
|---|---|
| `billboards/models.py` | `specifications` JSONField |
| `billboards/migrations/0013_billboard_specifications.py` | DB migration |
| `billboards/specifications_utils.py` | Parse string → dict, size check |
| `billboards/serializers.py` | `SpecificationsJSONField` on create/read serializers |

---

## Why we needed `specifications`

1. **Different types, different shapes** — Digital needs slots; Static needs monthly pricing. One fixed schema does not fit all.
2. **Avoid schema explosion** — Without JSON we would add columns like `loop_duration`, `slot_1_status`, … for every new media type.
3. **Frontend owns the contract per type** — Flutter builds the JSON based on `ooh_media_type`. Backend stores and returns it without hard-coding every field.
4. **Fast to ship** — No pivot tables or booking engine required for MVP; booking can be added later.
5. **Backward compatible** — Old billboards get `"specifications": {}`. Map/list endpoints stay minimal.

---

## Before vs after API responses

### POST `/api/billboards/` — Create

**Before (still the same response shape):**

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

Create response did **not** include billboard body before; it still does **not** after. Fetch detail with `GET /api/billboards/{id}/`.

**Before:** `specifications` was ignored / did not exist in DB.

**After:** `specifications` is saved when sent in the form.

---

### GET `/api/billboards/{id}/` — Detail

**Before:**

```json
{
  "id": 20,
  "city": "Lahore",
  "ooh_media_type": "Digital Billboard",
  "type": "Premium",
  "price_range": "8000",
  "exposure_time": "per 10 sec",
  "latitude": 31.5204,
  "longitude": 74.3587,
  "images": [],
  "availability": {
    "booked_dates": [],
    "total_booked": 0
  },
  "approval_status": "approved",
  "is_in_wishlist": false
}
```

**After (digital example):**

```json
{
  "id": 40,
  "city": "Lahore",
  "ooh_media_type": "Digital Billboard",
  "type": "Premium",
  "price_range": "8000",
  "exposure_time": "per 10 sec",
  "latitude": 31.52,
  "longitude": 74.35,
  "images": [],
  "specifications": {
    "loop_duration_seconds": 60,
    "allowed_video_lengths": [10, 20, 30, 40, 60],
    "price_per_second": 800,
    "currency": "PKR",
    "slots": [
      { "slot_number": 1, "duration_seconds": 10, "status": "booked" },
      { "slot_number": 2, "duration_seconds": 10, "status": "booked" },
      { "slot_number": 3, "duration_seconds": 20, "status": "booked" },
      { "slot_number": 4, "duration_seconds": 0, "status": "open" },
      { "slot_number": 5, "duration_seconds": 0, "status": "open" }
    ]
  },
  "availability": {
    "booked_dates": [],
    "total_booked": 0
  },
  "approval_status": "approved",
  "is_in_wishlist": false
}
```

**After (static example):**

```json
{
  "id": 41,
  "ooh_media_type": "Static Billboard",
  "specifications": {
    "price_per_month": 40000,
    "printing_cost": 5000,
    "currency": "PKR"
  }
}
```

**After (legacy billboard with no specs):**

```json
{
  "id": 20,
  "ooh_media_type": "Static Billboard",
  "specifications": {}
}
```

---

### GET `/api/billboards/my-billboards/`

**Before / after:** Same paginated list shape; each item in `results[]` now includes `"specifications": { ... }` or `{}`.

---

### GET `/api/billboards/` (map)

**Unchanged** — still returns only `{ id, latitude, longitude, count }` (or clusters). No `specifications` on map pins (by design).

---

### GET `/api/billboards/{id}/preview/`

**Unchanged** — lightweight preview does not include full `specifications`. Use detail API for booking UI.

---

## Recommended `specifications` shapes (frontend convention)

Backend accepts **any JSON object**. These are recommended conventions:

### Digital (`ooh_media_type = "Digital Billboard"`)

```json
{
  "loop_duration_seconds": 60,
  "allowed_video_lengths": [10, 20, 30, 40, 60],
  "price_per_second": 800,
  "currency": "PKR",
  "slots": [
    { "slot_number": 1, "duration_seconds": 10, "status": "booked" },
    { "slot_number": 4, "duration_seconds": 0, "status": "open" }
  ]
}
```

### Static (`ooh_media_type = "Static Billboard"`)

```json
{
  "price_per_month": 40000,
  "printing_cost": 5000,
  "currency": "PKR"
}
```

Flutter logic:

```dart
final specs = oohMediaType.toLowerCase().contains('digital')
    ? buildDigitalSpecs(...)
    : buildStaticSpecs(...);

formData.fields.add(MapEntry('specifications', jsonEncode(specs)));
```

---

## API reference

### POST `/api/billboards/` — Create billboard

| Item | Value |
|---|---|
| Auth | Bearer token (media owner) |
| Content-Type | `multipart/form-data` |

**Common form fields:** `city`, `ooh_media_type`, `type`, `latitude`, `longitude`, `road_name`, `description`, `price_range`, `exposure_time`, `display_width`, `display_height`, `company_name`, `advertiser_phone`, `generator_backup`, `specifications` (JSON string), `images_0`, `images_1`, …

**Not accepted on create:** `unavailable_dates`, `booked_dates`, `availability` (use availability API after create).

#### curl — Digital

```bash
BASE_URL="http://16.16.160.64:8000"
TOKEN="YOUR_MEDIA_OWNER_ACCESS_TOKEN"

curl --location "$BASE_URL/api/billboards/" \
  --header "Authorization: Bearer $TOKEN" \
  --form 'city="Lahore"' \
  --form 'ooh_media_type="Digital Billboard"' \
  --form 'type="Premium"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'road_name="Jail Road"' \
  --form 'price_range="8000"' \
  --form 'exposure_time="per 10 sec"' \
  --form 'specifications="{\"loop_duration_seconds\":60,\"allowed_video_lengths\":[10,20,30,40,60],\"price_per_second\":800,\"currency\":\"PKR\",\"slots\":[{\"slot_number\":1,\"duration_seconds\":10,\"status\":\"booked\"},{\"slot_number\":4,\"duration_seconds\":0,\"status\":\"open\"}]}"' \
  --form 'images_0=@"/path/to/photo.jpg"'
```

**Expected response — 201:**

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

#### curl — Static

```bash
curl --location "$BASE_URL/api/billboards/" \
  --header "Authorization: Bearer $TOKEN" \
  --form 'city="Lahore"' \
  --form 'ooh_media_type="Static Billboard"' \
  --form 'type="Premium"' \
  --form 'latitude="31.4544"' \
  --form 'longitude="74.2638"' \
  --form 'price_range="40000"' \
  --form 'exposure_time="per month"' \
  --form 'specifications="{\"price_per_month\":40000,\"printing_cost\":5000,\"currency\":\"PKR\"}"' \
  --form 'images_0=@"/path/to/photo.jpg"'
```

---

### GET `/api/billboards/{id}/` — Detail

```bash
curl --location "$BASE_URL/api/billboards/40/" \
  --header "Authorization: Bearer $TOKEN"
```

**Expected response — 200:** Full billboard object including `specifications` (see examples above).

---

### PUT / PATCH `/api/billboards/{id}/` — Update

Same as create; include `specifications` to replace the whole object.

```bash
curl --location --request PATCH "$BASE_URL/api/billboards/40/" \
  --header "Authorization: Bearer $TOKEN" \
  --form 'specifications="{\"loop_duration_seconds\":60,\"price_per_second\":900,\"currency\":\"PKR\",\"slots\":[]}"'
```

**Expected response — 200:** Updated full billboard JSON (DRF default update response).

---

### GET `/api/billboards/my-billboards/` — Owner list

```bash
curl --location "$BASE_URL/api/billboards/my-billboards/?page_size=10" \
  --header "Authorization: Bearer $TOKEN"
```

**Expected response — 200:**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 40,
      "city": "Lahore",
      "ooh_media_type": "Digital Billboard",
      "specifications": { "...": "..." },
      "availability": { "booked_dates": [], "total_booked": 0 }
    }
  ]
}
```

---

## HTTP status codes

| Code | When | Example body |
|---|---|---|
| **201** | Billboard created | `{ "status_code": 201, "message": "Billboard created successfully" }` |
| **200** | Detail, list, update success | Full JSON object or paginated list |
| **400** | Invalid `specifications` JSON | `{ "specifications": ["specifications must be valid JSON."] }` |
| **400** | `specifications` not an object | `{ "specifications": ["specifications must be a JSON object."] }` |
| **400** | Payload too large (>20 KB) | `{ "specifications": ["specifications exceeds maximum size of 20480 bytes."] }` |
| **400** | Validation error on other fields | `{ "city": ["This field is required."] }` |
| **401** | Missing/invalid token | `{ "detail": "Authentication credentials were not provided." }` |
| **403** | Advertiser tries to create | `{ "detail": "Only media owners can create billboards..." }` |
| **403** | Update someone else's billboard | `{ "detail": "You can only update your own billboards." }` |
| **404** | Billboard not found | `{ "detail": "Not found." }` |
| **415** | JSON body instead of multipart on create | `{ "detail": "Unsupported media type..." }` |

---

## Flutter checklist

1. Use **`ooh_media_type`** to pick digital vs static form (not a separate kind field).
2. Build `specifications` map in Dart → `jsonEncode` → form field `specifications`.
3. After create **201**, call `GET /api/billboards/{id}/` for full data including specs.
4. On detail / my-billboards, read `specifications` and render type-specific booking UI.
5. Date availability stays separate: `PUT /api/billboards/{id}/availability/` with `booked_dates`.

---

## Deployment

On production after pull:

```bash
cd /path/to/Reachtolet_backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart reachtolet-gunicorn
```

Verify:

```bash
curl "$BASE_URL/api/users/health/"
```

---

## Postman

1. Method: **POST**
2. URL: `{{base_url}}/api/billboards/`
3. Auth: Bearer `{{access_token}}`
4. Body: **form-data**
   - Key `specifications`, type **Text**, value = JSON string
   - Key `images_0`, type **File**

---

## Related docs

- `BILLBOARD_PREVIEW_API_GUIDE.md` — Map pin preview (no specifications)
- Availability: `PUT /api/billboards/{id}/availability/` — date-based booking for static boards
