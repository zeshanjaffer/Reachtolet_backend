# Create Billboard API Guide

**Multipart only** — upload images as files, not JSON body.

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `http://16.16.160.64:8000/api/billboards/` |
| **Content-Type** | `multipart/form-data` |
| **Auth** | `Authorization: Bearer {access_token}` |
| **Role** | `media_owner` only |

---

## How image upload works

1. Flutter sends **`multipart/form-data`** (not `application/json`).
2. Text fields go in **form fields** (`city`, `latitude`, …).
3. Image files use file keys **`images_0`**, **`images_1`**, **`images_2`**, …
4. Server saves each file → builds public URLs → stores them in DB field `images` (JSON array of URLs).
5. **Do not** send an `images` form field from Flutter unless it is a JSON string of existing URLs.  
   Sending `images: ""` or `images: []` as a text field caused the old `"Value must be valid JSON"` error (fixed on server).

### Image field rules

| Item | Value |
|---|---|
| File keys | `images_0`, `images_1`, `images_2`, … |
| Max size | 10 MB per file |
| Types | JPEG, PNG, GIF, WebP |
| Method | `POST` multipart file parts |

---

## curl — create with 2 images

```bash
curl --location "http://16.16.160.64:8000/api/billboards/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'city="Lahore"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'price_range="8000"' \
  --form 'media_type_id="3"' \
  --form 'type="Premium"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_second\":800,\"loop_duration_seconds\":60,\"allowed_video_lengths\":[10,20,30],\"slots\":[]}"' \
  --form 'images_0=@"/path/to/photo1.jpg"' \
  --form 'images_1=@"/path/to/photo2.jpg"'
```

> **Media type id:** call `GET /api/billboards/media-types/` first (see `BILLBOARD_MEDIA_TYPES_GUIDE.md`).  
> Example: `3` = Digital Billboard, `12` = Bus Shelter, `21` = Mall Advertising.

## curl — create without images

```bash
curl --location "http://16.16.160.64:8000/api/billboards/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'city="Karachi"' \
  --form 'latitude="24.8607"' \
  --form 'longitude="67.0011"' \
  --form 'price_range="150000"' \
  --form 'media_type_id="9"' \
  --form 'type="Standard"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_month\":150000}"'
```

---

## Responses & status codes

### 201 Created — success

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

Then fetch full record:

```http
GET /api/billboards/{id}/
```

Example `images` on detail:

```json
{
  "id": 42,
  "city": "Lahore",
  "images": [
    "http://16.16.160.64:8000/media/billboards/abc123.jpg",
    "http://16.16.160.64:8000/media/billboards/def456.jpg"
  ],
  "latitude": 31.5204,
  "longitude": 74.3587,
  "ooh_media_type": "Digital Billboard",
  "media_type_detail": {
    "id": 3,
    "name": "Digital Billboard",
    "slug": "digital-billboard",
    "category": "digital",
    "is_digital": true
  },
  "specifications": { "currency": "PKR", "slots": [] }
}
```

---

### 401 Unauthorized

Missing or invalid token.

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 403 Forbidden — not media owner

```json
{
  "detail": "Only media owners can create billboards. You are registered as an advertiser."
}
```

---

### 400 Bad Request — validation

Missing required field:

```json
{
  "media_type_id": ["This field is required. Pick a type from GET /api/billboards/media-types/."]
}
```

Or:

```json
{
  "city": ["This field is required."]
}
```

Invalid `specifications` JSON string:

```json
{
  "specifications": ["specifications must be valid JSON."]
}
```

---

### 400 — bad image file type

```json
{
  "detail": "Invalid file type for images_0: application/pdf"
}
```

---

### 400 — image too large

```json
{
  "detail": "File too large for images_1. Maximum size is 10MB."
}
```

---

### 500 — upload failed

```json
{
  "detail": "Upload failed for images_0: ..."
}
```

---

## Required form fields

| Field | Example |
|---|---|
| `city` | `Lahore` |
| `latitude` | `31.5204` |
| `longitude` | `74.3587` |
| `media_type_id` | `3` (from `GET /api/billboards/media-types/`) |
| `type` | `Premium` or `Standard` |
| `price_range` | `8000` |

`latitude` + `longitude` are required for the billboard to appear on the map.

---

## `specifications` (multipart)

Send as a **JSON string** in one form field named `specifications`:

**Digital:**

```json
{
  "currency": "PKR",
  "price_per_second": 800,
  "loop_duration_seconds": 60,
  "allowed_video_lengths": [10, 20, 30],
  "slots": []
}
```

**Static:**

```json
{
  "currency": "PKR",
  "price_per_month": 150000,
  "printing_cost": 25000
}
```

---

## Flutter example (correct)

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

Future<void> createBillboard({
  required String accessToken,
  required String city,
  required double latitude,
  required double longitude,
  required int mediaTypeId,
  required String type,
  required String priceRange,
  required Map<String, dynamic> specifications,
  List<File> imageFiles = const [],
}) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('$baseUrl/api/billboards/'),
  );

  request.headers['Authorization'] = 'Bearer $accessToken';

  // Text fields only — NOT a JSON body
  request.fields['city'] = city;
  request.fields['latitude'] = latitude.toString();
  request.fields['longitude'] = longitude.toString();
  request.fields['media_type_id'] = mediaTypeId.toString();
  request.fields['type'] = type;
  request.fields['price_range'] = priceRange;
  request.fields['specifications'] = jsonEncode(specifications);

  // Files — images_0, images_1, ...
  for (var i = 0; i < imageFiles.length; i++) {
    request.files.add(
      await http.MultipartFile.fromPath('images_$i', imageFiles[i].path),
    );
  }

  // DO NOT add: request.fields['images'] = '' or '[]'

  final response = await http.Response.fromStream(await request.send());

  if (response.statusCode != 201) {
    throw Exception('Create failed: ${response.statusCode} ${response.body}');
  }
}
```

---

## Update billboard — PATCH / PUT

Same auth and multipart rules as create. Use `media_type_id` to change the media type.

```bash
curl --location --request PATCH "http://16.16.160.64:8000/api/billboards/46/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'media_type_id="12"' \
  --form 'price_range="120000"'
```

**200 OK** — returns full updated billboard JSON with `media_type_detail`.

| HTTP | Cause |
|---|---|
| **200** | Updated successfully |
| **400** | Invalid `media_type_id` |
| **403** | Not the billboard owner |
| **404** | Billboard not found |

`ooh_media_type` is read-only on update. New `images_0` files are appended; send `images` as JSON string to replace the full list.

See `BILLBOARD_MEDIA_TYPES_GUIDE.md` for full update examples.

---

## Do NOT send

| Bad | Why |
|---|---|
| `Content-Type: application/json` | Use multipart only |
| `images` empty text field | Was causing JSON validation error (server fixed; still avoid) |
| `images_0` as text field | Must be a **file** part |
| `ooh_media_type` on create/update | Use `media_type_id` from picker instead |
| `booked_dates` / `availability` on create/update | Use `PUT /api/billboards/{id}/availability/` |

---

## Map visibility after create

Billboard shows on map when:

1. `latitude` and `longitude` sent  
2. `is_active` = true (default)  
3. `approval_status` = approved (auto if `BYPASS_BILLBOARD_APPROVAL` is on)  
4. Map API called with JWT + all 4 bounds  

---

## Related

- `BILLBOARD_MEDIA_TYPES_GUIDE.md` — picker API, all type ids, before/after create flow
- `BILLBOARD_SPECIFICATIONS_GUIDE.md` — digital vs static JSON shapes  
- `BILLBOARD_SEARCH_FILTER_API_GUIDE.md` — map list API
