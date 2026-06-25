# Billboard Media Types — API & Implementation Guide

**Base URL:** `http://16.16.160.64:8000`

This guide covers the new **OOH media type catalog** (adbuq-style picker), the **media type picker API**, and the **before/after** change to **Create Billboard**.

---

## Overview

| What | Detail |
|---|---|
| **New table** | `OohMediaType` — 28 rows (2 group headers + 26 selectable types) |
| **Billboard link** | `Billboard.media_type` FK → `OohMediaType` |
| **Legacy field** | `ooh_media_type` string kept for search/filters; auto-synced from `media_type.name` on save |
| **Picker API** | `GET /api/billboards/media-types/` (media owners only) |
| **Create change** | Send `media_type_id` (integer) instead of free-text `ooh_media_type` |

---

## Implementation plan (before → after)

### Database

| Before | After |
|---|---|
| No media type table | `OohMediaType` model with `name`, `slug`, `category`, `parent`, `is_selectable`, `is_digital`, `sort_order` |
| `Billboard.ooh_media_type` only (free text) | `Billboard.media_type` FK + `ooh_media_type` synced on save |
| Types hard-coded in app / typos possible | 26 seeded types from adbuq screenshots + market standards |

### Create Billboard flow

```
BEFORE:
  Media owner → types ooh_media_type string manually → POST /api/billboards/

AFTER:
  1. Media owner → GET /api/billboards/media-types/
  2. UI shows grouped picker (Digital / Static / Place / Transit)
  3. User selects one type → store id
  4. POST /api/billboards/ with media_type_id={id}
  5. Server sets media_type FK + syncs ooh_media_type string
```

### Search / filter

| Before | After |
|---|---|
| `?ooh_media_type=Digital Billboard` | Still works (legacy) |
| — | `?media_type_id=3` (preferred) |

### API responses (detail / list)

| Before | After |
|---|---|
| `ooh_media_type: "Digital Billboard"` only | Same + `media_type_detail: { id, name, slug, category, is_digital }` |

---

## Seeded media types (full list)

### Group headers (not selectable — picker UI only)

| id | name | slug |
|---|---|---|
| 1 | All Digital | `all-digital` |
| 2 | All Static | `all-static` |

### Selectable types

| id | name | category | is_digital |
|---|---|---|---|
| 3 | Digital Billboard | digital | true |
| 4 | Digital Pole Signs | digital | true |
| 5 | Digital Pylon | digital | true |
| 6 | Digital SMD | digital | true |
| 7 | LED Video Wall | digital | true |
| 8 | Mall Digital Screen | digital | true |
| 9 | Static Billboard | static | false |
| 10 | Billboards | static | false |
| 11 | Bridge Banner | static | false |
| 12 | Bus Shelter | static | false |
| 13 | Pole Signs | static | false |
| 14 | Wall Panels | static | false |
| 15 | Hoarding | static | false |
| 16 | Unipole | static | false |
| 17 | Gantry | static | false |
| 18 | Rooftop Billboard | static | false |
| 19 | Wallscape | static | false |
| 20 | Airport Advertising | place | false |
| 21 | Mall Advertising | place | false |
| 22 | Cinema Advertising | place | false |
| 23 | Metro Station Advertising | place | false |
| 24 | Railway Platform Advertising | place | false |
| 25 | Vehicle Branding | transit | false |
| 26 | Bus Wrap | transit | false |
| 27 | Taxi Branding | transit | false |
| 28 | Mopy | transit | false |

Use `is_digital: true` on the client to show the **digital specifications** form; `false` → static pricing form. See `BILLBOARD_SPECIFICATIONS_GUIDE.md`.

---

## 1. Media type picker API

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `/api/billboards/media-types/` |
| **Query** | `search` (optional) — partial match on type `name` or `slug` |
| **Auth** | `Authorization: Bearer {access_token}` |
| **Role** | `media_owner` only |

### curl — full list

```bash
BASE_URL="http://16.16.160.64:8000"
ACCESS="MEDIA_OWNER_JWT"

curl --location "${BASE_URL}/api/billboards/media-types/" \
  --header "Authorization: Bearer ${ACCESS}"
```

### curl — search (e.g. "bus")

```bash
curl --location "${BASE_URL}/api/billboards/media-types/?search=bus" \
  --header "Authorization: Bearer ${ACCESS}"
```

Matches **Bus Shelter**, **Bus Wrap**, etc. Search is case-insensitive.

### 200 OK — success

```json
{
  "status_code": 200,
  "message": "Media types retrieved successfully",
  "search": null,
  "count": 26,
  "groups": [
    {
      "key": "digital",
      "label": "Digital",
      "header": {
        "id": 1,
        "name": "All Digital",
        "slug": "all-digital",
        "is_selectable": false
      },
      "types": [
        {
          "id": 3,
          "name": "Digital Billboard",
          "slug": "digital-billboard",
          "category": "digital",
          "is_digital": true
        }
      ]
    },
    {
      "key": "static",
      "label": "Static",
      "header": {
        "id": 2,
        "name": "All Static",
        "slug": "all-static",
        "is_selectable": false
      },
      "types": [
        {
          "id": 9,
          "name": "Static Billboard",
          "slug": "static-billboard",
          "category": "static",
          "is_digital": false
        }
      ]
    },
    {
      "key": "place",
      "label": "Place Based",
      "header": null,
      "types": [
        {
          "id": 20,
          "name": "Airport Advertising",
          "slug": "airport-advertising",
          "category": "place",
          "is_digital": false
        }
      ]
    },
    {
      "key": "transit",
      "label": "Transit & Mobile",
      "header": null,
      "types": [
        {
          "id": 25,
          "name": "Vehicle Branding",
          "slug": "vehicle-branding",
          "category": "transit",
          "is_digital": false
        }
      ]
    }
  ],
  "selectable": [
    {
      "id": 3,
      "name": "Digital Billboard",
      "slug": "digital-billboard",
      "category": "digital",
      "is_digital": true
    }
  ]
}
```

**Response fields:**

| Field | Use |
|---|---|
| `groups` | adbuq-style UI: section headers + nested types |
| `selectable` | Flat list for simple dropdowns / search |
| `count` | Number of selectable types (after search filter) |
| `search` | Echo of `?search=` query, or `null` if omitted |

### 200 OK — search example (`?search=bus`)

```json
{
  "status_code": 200,
  "message": "Media types matching \"bus\" retrieved successfully",
  "search": "bus",
  "count": 2,
  "groups": [
    {
      "key": "static",
      "label": "Static",
      "header": { "id": 2, "name": "All Static", "slug": "all-static", "is_selectable": false },
      "types": [
        { "id": 12, "name": "Bus Shelter", "slug": "bus-shelter", "category": "static", "is_digital": false }
      ]
    },
    {
      "key": "transit",
      "label": "Transit & Mobile",
      "header": null,
      "types": [
        { "id": 26, "name": "Bus Wrap", "slug": "bus-wrap", "category": "transit", "is_digital": false }
      ]
    }
  ],
  "selectable": [
    { "id": 12, "name": "Bus Shelter", "slug": "bus-shelter", "category": "static", "is_digital": false },
    { "id": 26, "name": "Bus Wrap", "slug": "bus-wrap", "category": "transit", "is_digital": false }
  ]
}
```

Empty search with no matches still returns **200** with `"count": 0`, `"groups": []`, `"selectable": []`.

### Picker status codes

| HTTP | When | Body |
|---|---|---|
| **200** | Success | Full JSON above |
| **401** | No/invalid JWT | `{"detail": "Authentication credentials were not provided."}` |
| **403** | User is `advertiser` | `{"detail": "Only media owners can perform this action."}` |

---

## 2. Create Billboard — BEFORE vs AFTER

### BEFORE (deprecated)

```bash
curl --location "${BASE_URL}/api/billboards/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --form 'city="Lahore"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'price_range="80000"' \
  --form 'ooh_media_type="Digital Billboard"' \
  --form 'type="Premium"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_second\":800,\"loop_duration_seconds\":60,\"allowed_video_lengths\":[10,20,30],\"slots\":[]}"'
```

Problems: typos in `ooh_media_type`, no stable id, hard to filter consistently.

### AFTER (required)

**Step 1** — load picker, user picks e.g. **Bus Shelter** → `id: 12`

**Step 2** — create with `media_type_id`:

```bash
curl --location "${BASE_URL}/api/billboards/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --form 'city="Lahore"' \
  --form 'latitude="31.5204"' \
  --form 'longitude="74.3587"' \
  --form 'price_range="120000"' \
  --form 'media_type_id="12"' \
  --form 'type="Standard"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_month\":120000}"' \
  --form 'images_0=@"/path/to/photo.jpg"'
```

### 201 Created

```json
{
  "status_code": 201,
  "message": "Billboard created successfully"
}
```

### GET detail — after create

```bash
curl --location "${BASE_URL}/api/billboards/46/" \
  --header "Authorization: Bearer ${ACCESS}"
```

```json
{
  "id": 46,
  "city": "Lahore",
  "ooh_media_type": "Digital Billboard",
  "media_type_detail": {
    "id": 3,
    "name": "Digital Billboard",
    "slug": "digital-billboard",
    "category": "digital",
    "is_digital": true
  },
  "type": "Premium",
  "price_range": "50000",
  "latitude": 31.5204,
  "longitude": 74.3587,
  "specifications": {
    "currency": "PKR",
    "price_per_second": 500,
    "loop_duration_seconds": 60,
    "allowed_video_lengths": [10, 20],
    "slots": []
  }
}
```

Note: `ooh_media_type` is **read-only** on write; it is set automatically from the selected `media_type`.

---

## 3. Update Billboard — PATCH / PUT

| | |
|---|---|
| **Method** | `PATCH` (partial) or `PUT` (full) |
| **URL** | `/api/billboards/{id}/` |
| **Content-Type** | `multipart/form-data` (Flutter) or `application/json` |
| **Auth** | `media_owner` JWT — own billboards only |

### BEFORE (deprecated)

```bash
curl --location --request PATCH "${BASE_URL}/api/billboards/46/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --form 'ooh_media_type="Static Billboard"'
```

### AFTER — change media type by id

```bash
curl --location --request PATCH "${BASE_URL}/api/billboards/46/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --form 'media_type_id="9"'
```

`ooh_media_type` and `media_type_detail` update automatically after save.

### JSON PATCH (also supported)

```bash
curl --location --request PATCH "${BASE_URL}/api/billboards/46/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --header "Content-Type: application/json" \
  --data '{"media_type_id": 12, "price_range": "120000"}'
```

### Multipart — update type + specs + append image

New `images_0` files are **appended** to existing images. Send an `images` JSON string to **replace** the full list.

```bash
curl --location --request PATCH "${BASE_URL}/api/billboards/46/" \
  --header "Authorization: Bearer ${ACCESS}" \
  --form 'media_type_id="3"' \
  --form 'price_range="85000"' \
  --form 'specifications="{\"currency\":\"PKR\",\"price_per_second\":850,\"loop_duration_seconds\":60,\"slots\":[]}"' \
  --form 'images_0=@"/path/to/new-photo.jpg"'
```

### 200 OK — update response

Returns the **full updated billboard** JSON (same shape as GET detail), including `media_type_detail`.

### Update status codes

| HTTP | Cause | Example |
|---|---|---|
| **200** | Updated | Full billboard JSON |
| **400** | Invalid `media_type_id` | `{"media_type_id": ["Invalid pk \"99\" - object does not exist."]}` |
| **401** | No JWT | `{"detail": "Authentication credentials were not provided."}` |
| **403** | Not owner / advertiser | `{"detail": "You can only update your own billboards."}` |
| **404** | Billboard not found | `{"detail": "Not found."}` |

`ooh_media_type` cannot be set directly on update — use `media_type_id`.

---

## 4. Create Billboard — status codes & messages

| HTTP | Cause | Example response |
|---|---|---|
| **201** | Created | `{"status_code": 201, "message": "Billboard created successfully"}` |
| **400** | Missing `media_type_id` | `{"media_type_id": ["This field is required. Pick a type from GET /api/billboards/media-types/."]}` |
| **400** | Invalid / inactive type id | `{"media_type_id": ["Invalid pk \"99\" - object does not exist."]}` |
| **400** | Group header id (1 or 2) | `{"media_type_id": ["Invalid pk \"1\" - object does not exist."]}` |
| **400** | Missing `city` / other required fields | `{"city": ["This field is required."]}` |
| **400** | Bad `specifications` JSON | `{"specifications": ["specifications must be valid JSON."]}` |
| **400** | Bad image type / size | `{"detail": "Invalid file type for images_0: ..."}` |
| **401** | No JWT | `{"detail": "Authentication credentials were not provided."}` |
| **403** | Advertiser tries create | `{"detail": "Only media owners can create billboards. You are registered as an advertiser."}` |
| **500** | Upload failure | `{"detail": "Upload failed for images_0: ..."}` |

### Legacy fallback (temporary)

If you still send `ooh_media_type` **without** `media_type_id`, the server tries to match an active type by name (case-insensitive). **Prefer `media_type_id`** for all new app builds.

---

## 5. Filter billboards by media type

```bash
# Preferred
curl "${BASE_URL}/api/billboards/?media_type_id=3&page_size=10" \
  -H "Authorization: Bearer ${ACCESS}"

# Legacy (still supported)
curl "${BASE_URL}/api/billboards/?ooh_media_type=Digital%20Billboard" \
  -H "Authorization: Bearer ${ACCESS}"
```

Works on map list, paginated list, and `my-billboards/`.

---

## 6. Flutter integration checklist

1. On **Add / Edit Billboard** → `GET /api/billboards/media-types/` (optional `?search=bus`)
2. Build multi-select or single-select from `groups` or `selectable`
3. Store selected **`id`** (not name string)
4. If `is_digital == true` → show digital specs form; else static specs form
5. **Create:** `POST /api/billboards/` with `media_type_id`
6. **Update:** `PATCH /api/billboards/{id}/` with `media_type_id` to change type
7. On detail / my-billboards read `media_type_detail` for display

```dart
// Example: after picker load
final selectedTypeId = 12; // Bus Shelter

request.fields['media_type_id'] = selectedTypeId.toString();
// Do NOT send ooh_media_type on new builds
```

---

## 7. Admin

Django admin: **Billboards → OOH media types** — add/edit/deactivate types without code deploy.

Billboard admin shows `media_type` FK alongside synced `ooh_media_type`.

---

## Related guides

- `BILLBOARD_CREATE_API_GUIDE.md` — multipart create, images, full field list
- `BILLBOARD_SPECIFICATIONS_GUIDE.md` — digital vs static JSON
- `BILLBOARD_SEARCH_FILTER_API_GUIDE.md` — map bounds + filters
- `COMPLETE_API_GUIDE.md` — full REST reference
