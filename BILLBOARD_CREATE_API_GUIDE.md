# Create Billboard API — Multipart + Images (Flutter)

**Media owner only.** Use **`multipart/form-data`** — not JSON.

**Base URL:** `http://16.16.160.64:8000`  
**Endpoint:** `POST /api/billboards/`  
**Auth:** `Authorization: Bearer {access_token}`

---

## Success response

**201 Created**

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

Then load full data: `GET /api/billboards/{id}/`

---

## Errors

| HTTP | Meaning |
|---|---|
| **401** | No / invalid token |
| **403** | User is `advertiser`, not `media_owner` |
| **400** | Missing field, bad image type, file too large |

---

## Required form fields

| Field | Example |
|---|---|
| `city` | `Lahore` |
| `latitude` | `31.5204` |
| `longitude` | `74.3587` |
| `ooh_media_type` | `Digital Billboard` or `Static Billboard` |
| `type` | `Premium` or `Standard` |
| `price_range` | `8000` |

**`latitude` + `longitude` are required** for the billboard to show on the map.

---

## Images — how to upload

### Field names

Use **`images_0`**, **`images_1`**, **`images_2`**, … (any key starting with `images`).

| Rule | Value |
|---|---|
| Max size per file | **10 MB** |
| Allowed types | JPEG, PNG, GIF, WebP |
| Multiple files | `images_0`, `images_1`, … |

Server saves files and stores URLs in the billboard `images` array.

### curl with one image

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
  --form 'images_0=@"/path/to/photo1.jpg"'
```

### curl with multiple images

```bash
curl --location "http://16.16.160.64:8000/api/billboards/" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN" \
  --form 'city="Lahore"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'price_range="8000"' \
  --form 'ooh_media_type="Static Billboard"' \
  --form 'type="Standard"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_month\":150000,\"printing_cost\":25000}"' \
  --form 'images_0=@"/path/to/front.jpg"' \
  --form 'images_1=@"/path/to/side.jpg"'
```

### Flutter (multipart + images)

```dart
import 'package:http/http.dart' as http;
import 'dart:io';

Future<void> createBillboardWithImages({
  required String accessToken,
  required String city,
  required double latitude,
  required double longitude,
  required String oohMediaType,
  required String type,
  required String priceRange,
  required String specificationsJson,
  required List<File> imageFiles,
}) async {
  final uri = Uri.parse('$baseUrl/api/billboards/');
  final request = http.MultipartRequest('POST', uri);

  request.headers['Authorization'] = 'Bearer $accessToken';

  request.fields['city'] = city;
  request.fields['latitude'] = latitude.toString();
  request.fields['longitude'] = longitude.toString();
  request.fields['ooh_media_type'] = oohMediaType;
  request.fields['type'] = type;
  request.fields['price_range'] = priceRange;
  request.fields['specifications'] = specificationsJson;

  for (var i = 0; i < imageFiles.length; i++) {
    request.files.add(await http.MultipartFile.fromPath(
      'images_$i',
      imageFiles[i].path,
    ));
  }

  final streamed = await request.send();
  final response = await http.Response.fromStream(streamed);

  if (response.statusCode != 201) {
    throw Exception('Create failed: ${response.statusCode} ${response.body}');
  }
}
```

### `specifications` in multipart

Must be a **JSON string** in the form field (not a separate JSON body):

```dart
request.fields['specifications'] = jsonEncode({
  'currency': 'PKR',
  'price_per_second': 800,
  'loop_duration_seconds': 60,
  'allowed_video_lengths': [10, 20, 30],
  'slots': [],
});
```

---

## Optional text fields

`description`, `road_name`, `exposure_time`, `display_width`, `display_height`,  
`advertiser_phone`, `advertiser_whatsapp`, `company_name`, `company_website`,  
`address`, `generator_backup` (`Yes` / `No`)

---

## Do NOT send

| Field | Use instead |
|---|---|
| `booked_dates` | `PUT /api/billboards/{id}/availability/` |
| `availability` | Read-only on GET |
| JSON body | Use multipart only |

---

## Map visibility checklist

After create, billboard shows on map when:

1. `latitude` and `longitude` sent in form  
2. `is_active` = true (default)  
3. `approval_status` = approved (auto if `BYPASS_BILLBOARD_APPROVAL` is on)  
4. Map API called with valid JWT + all 4 bounds (`ne_lat`, `ne_lng`, `sw_lat`, `sw_lng`)

---

## Related

- `BILLBOARD_SPECIFICATIONS_GUIDE.md` — digital vs static `specifications` shapes  
- `BILLBOARD_SEARCH_FILTER_API_GUIDE.md` — map fetch while dragging
