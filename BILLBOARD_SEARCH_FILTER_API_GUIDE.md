# Billboard Search & Filter API Guide

Complete reference for **search** and **filter** on billboard list endpoints.  
Use this guide when implementing map search, filter chips, and list views in the Next.js website.

**Base URL:** `http://16.16.160.64:8000`  
**Auth:** All endpoints require `Authorization: Bearer {access_token}`

---

## Overview

Search and filter are **not separate URLs**. They are query parameters on existing list endpoints:

| Endpoint | Use case | Response shape |
|---|---|---|
| `GET /api/billboards/` | Public map + advertiser discovery | Minimal markers `{ id, latitude, longitude, count }` or clusters |
| `GET /api/billboards/my-billboards/` | Media owner dashboard | Full billboard objects (paginated) |
| `GET /api/billboards/wishlist/` | Advertiser saved boards | Full billboard nested in wishlist item |

### Search vs filter

| Mechanism | Query param | Backend | Match type |
|---|---|---|---|
| **Search** | `search` | DRF `SearchFilter` | Case-insensitive **partial** match (`icontains`) across configured text fields |
| **Filter** | Field name params | Django Filter / custom logic | Exact or location-based rules (see tables below) |

Parameters can be **combined** (e.g. `search=Lahore&ooh_media_type=Digital Billboard&ne_lat=...`).

### PostGIS (production geo search)

Location filters use **PostGIS 3.3** on Supabase with a `location` geography column (GiST indexed):

| Feature | Implementation |
|---|---|
| Radius (`lat`, `lng`, `radius`) | True great-circle distance via `ST_DWithin` (km) |
| Map bounds | `ST_Within` on viewport polygon |
| Nearest first | Radius results auto-sorted nearest → farthest |
| Lat/lng API | Unchanged — `latitude` / `longitude` still returned; synced to `location` on save |

Billboards **without** coordinates are excluded from the map API (no `location`).

### Map drag — fixed on server

| Problem | Fix |
|---|---|
| Dummy billboards with null/wrong coords | **All old billboards deleted** from DB (clean slate) |
| Partial bounds while dragging (`ne_lat` only, etc.) | Returns **empty map JSON** (`clusters: []`), not paginated `links` shape |
| Inverted bounds on fast drag | PostGIS bounds **normalized** (swap NE/SW if flipped) |
| Null lat/lng in response | Map list only returns rows with valid `location` |

**Flutter:** always send all 4 bounds after drag ends (debounce 300–500 ms).  
`count: 0` with HTTP **200** is normal — not an error.

---

## HTTP status codes

| Code | When |
|---|---|
| **200** | Success (including zero results — empty `results` or `count: 0`) |
| **401** | Missing or invalid JWT |
| **403** | Advertiser calling `my-billboards` (media owner only) |

There is **no 400** for invalid filter values on these endpoints — unknown or non-matching filters typically return an empty list with **200**.

---

## 1. Public billboards — search & filter

**Endpoint:** `GET /api/billboards/`

**Base queryset (always applied):** only billboards where `is_active=true` AND `approval_status=approved`.

### All supported query parameters

| Parameter | Type | Purpose |
|---|---|---|
| `search` | string | Text search (see search fields below) |
| `ooh_media_type` | string | Filter by media type (case-insensitive exact) |
| `city` | string | Partial match on city (`icontains`) |
| `type` | string | Board tier: `Premium`, `Standard` (case-insensitive exact) |
| `ne_lat`, `ne_lng`, `sw_lat`, `sw_lng` | float | Map viewport bounds — **PostGIS** (priority over radius) |
| `lat`, `lng`, `radius` | float | **PostGIS** radius in **km**, nearest-first (when bounds not set) |
| `cluster` | `true` / `false` | Enable Supercluster clustering (map mode) |
| `zoom` | float | Map zoom 0–20 (default `10`; used with `cluster=true`) |
| `ordering` | string | Sort field; prefix `-` for descending |
| `page` | int | Page number (when **no** map bounds) |
| `page_size` | int | Items per page (default 20, max 100) |

### Search fields (`search` param)

Searches across these columns with **OR** logic (any field match):

| Field | Example match |
|---|---|
| `city` | `search=Lahore` → cities containing "Lahore" |
| `description` | `search=premium` → descriptions containing "premium" |
| `company_name` | `search=Acme` |
| `road_name` | `search=Mall Road` |

---

### 1.1 Text search only

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?search=Test" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK — paginated (no map bounds)**

```json
{
  "links": { "next": null, "previous": null },
  "count": 2,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 },
    { "id": 37, "latitude": 31.4544327089509, "longitude": 74.2638617880703, "count": 1 }
  ]
}
```

**200 OK — no matches**

```json
{
  "links": { "next": null, "previous": null },
  "count": 0,
  "total_pages": 1,
  "current_page": 1,
  "results": []
}
```

**401 Unauthorized**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 1.2 Filter by media type (`ooh_media_type`)

Supported values in database (use exact labels; matching is **case-insensitive**):

| Value | Description |
|---|---|
| `Digital Billboard` | Digital / LED boards |
| `Static Billboard` | Static / print boards |

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ooh_media_type=Digital%20Billboard" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ]
}
```

```bash
# Case-insensitive — also works
curl --location "http://16.16.160.64:8000/api/billboards/?ooh_media_type=digital%20billboard" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK — no boards of that type**

```json
{
  "links": { "next": null, "previous": null },
  "count": 0,
  "total_pages": 1,
  "current_page": 1,
  "results": []
}
```

---

### 1.3 Filter by map bounds (`ne_lat`, `ne_lng`, `sw_lat`, `sw_lng`) — PostGIS

When all four bounds are provided:

- Pagination is **disabled**
- Response returns all matching markers in the viewport (not paginated)
- Uses **PostGIS `ST_Within`** on the billboard `location` geography column
- Takes **priority** over `lat`/`lng`/`radius`

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ne_lat=32&ne_lng=75&sw_lat=31&sw_lng=74" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK — map bounds, no clustering**

```json
{
  "count": 2,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 },
    { "id": 37, "latitude": 31.4544327089509, "longitude": 74.2638617880703, "count": 1 }
  ],
  "clustering_enabled": false
}
```

---

### 1.4 Filter by radius (`lat`, `lng`, `radius`) — PostGIS

Used only when map bounds are **not** set.  
`radius` is in **kilometers** — true great-circle distance via PostGIS geography (`ST_DWithin`).

All three params required. Results are ordered **nearest first**.

Billboards without lat/lng (no `location` point) are excluded.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?lat=31.52&lng=74.35&radius=10" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ]
}
```

---

### 1.4b Filter by city (`city`)

Partial match (case-insensitive):

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?city=TestCity" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ]
}
```

---

### 1.4c Filter by board tier (`type`)

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?type=Premium" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — all approved active `Premium` boards (paginated).

---

Combine bounds with clustering for the map UI.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?cluster=true&zoom=10&ne_lat=35&ne_lng=77&sw_lat=28&sw_lng=70" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK — clustered map response**

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
      "type": "marker",
      "id": 37,
      "latitude": 31.4544327089509,
      "longitude": 74.2638617880703,
      "count": 1
    }
  ],
  "clustering_enabled": true,
  "zoom_level": 10.0
}
```

**Cluster item types**

| `type` | Fields | Meaning |
|---|---|---|
| `marker` | `id`, `latitude`, `longitude`, `count: 1` | Single billboard pin |
| `cluster` | `cluster_id`, `latitude`, `longitude`, `count`, `expansion_zoom` | Group of boards; zoom in to `expansion_zoom` |

---

### 1.6 Ordering (`ordering`)

Allowed fields: `created_at`, `price_range`, `city`, `views`  
Prefix with `-` for descending (default list order is `-created_at`).

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ordering=-created_at&page=1&page_size=5" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 3,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 },
    { "id": 37, "latitude": 31.4544327089509, "longitude": 74.2638617880703, "count": 1 },
    { "id": 20, "latitude": null, "longitude": null, "count": 1 }
  ]
}
```

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ordering=price_range" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 1.7 Combined search + filter + map bounds

All parameters are AND-ed together.

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?ne_lat=32&ne_lng=75&sw_lat=31&sw_lng=74&search=Test&ooh_media_type=Digital%20Billboard" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "count": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ],
  "clustering_enabled": false
}
```

```bash
# Search + media type + radius
curl --location "http://16.16.160.64:8000/api/billboards/?search=Lahore&ooh_media_type=Static%20Billboard&lat=31.5204&lng=74.3587&radius=25" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

```bash
# Search + filter + clustering on map move
curl --location "http://16.16.160.64:8000/api/billboards/?cluster=true&zoom=12&ne_lat=32&ne_lng=75&sw_lat=31&sw_lng=74&search=Test&ooh_media_type=Digital%20Billboard" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** (when clustering not dense enough, falls back to markers in `results`):

```json
{
  "count": 1,
  "results": [
    { "id": 40, "latitude": 31.52, "longitude": 74.35, "count": 1 }
  ],
  "clustering_enabled": false
}
```

---

### 1.8 Pagination (list view without map bounds)

```bash
curl --location "http://16.16.160.64:8000/api/billboards/?page=2&page_size=10&search=Lahore" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK**

```json
{
  "links": {
    "next": "http://16.16.160.64:8000/api/billboards/?page=3&page_size=10&search=Lahore",
    "previous": "http://16.16.160.64:8000/api/billboards/?page=1&page_size=10&search=Lahore"
  },
  "count": 25,
  "total_pages": 3,
  "current_page": 2,
  "results": [
    { "id": 15, "latitude": 31.48, "longitude": 74.30, "count": 1 }
  ]
}
```

> **Note:** Public list returns **minimal marker data only**. For full billboard details after user taps a result, call `GET /api/billboards/{id}/preview/` or `GET /api/billboards/{id}/`.

---

## 2. My billboards — search & filter (media owner)

**Endpoint:** `GET /api/billboards/my-billboards/`  
**Role:** `media_owner` only  
Returns **full** billboard objects (same fields as detail).

### All supported query parameters

| Parameter | Type | Purpose |
|---|---|---|
| `search` | string | Text search (fields below) |
| `city` | string | Exact match on city |
| `ooh_media_type` | string | Exact match (`Digital Billboard`, `Static Billboard`) |
| `type` | string | Exact match on board tier (`Premium`, `Standard`, etc.) |
| `is_active` | boolean | `true` or `false` |
| `approval_status` | string | `pending`, `approved`, or `rejected` |
| `ordering` | string | `created_at`, `price_range` (prefix `-` for desc) |
| `page`, `page_size` | int | Pagination |

### Search fields (`search` param)

| Field | Notes |
|---|---|
| `city` | Partial match |
| `description` | Partial match |
| `company_name` | Partial match |

> `road_name` is **not** searchable on this endpoint (unlike public list).

### Filter field values

| Filter | Example values |
|---|---|
| `city` | `Lahore`, `TestCity`, `Islamabad` (exact) |
| `ooh_media_type` | `Digital Billboard`, `Static Billboard` |
| `type` | `Premium`, `Standard` |
| `is_active` | `true`, `false` |
| `approval_status` | `pending`, `approved`, `rejected` |

---

### 2.1 Search my billboards

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?search=Test" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 2,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 40,
      "city": "TestCity",
      "description": null,
      "price_range": "8000",
      "ooh_media_type": "Digital Billboard",
      "type": "Premium",
      "latitude": 31.52,
      "longitude": 74.35,
      "is_active": true,
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "specifications": { "currency": "PKR", "price_per_second": 800 },
      "availability": { "booked_dates": [], "total_booked": 0 },
      "is_in_wishlist": false,
      "views": 0,
      "leads": 0,
      "created_at": "2026-06-13T10:41:51.409481Z"
    }
  ]
}
```

**403 Forbidden** (advertiser token)

```json
{
  "detail": "Only media owners can access their billboards. You are registered as an advertiser."
}
```

---

### 2.2 Filter by city

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?city=TestCity" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK** — paginated full objects; `count` reflects exact city match.

---

### 2.3 Filter by media type

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?ooh_media_type=Static%20Billboard" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 37,
      "city": "Lahore",
      "ooh_media_type": "Static Billboard",
      "type": "Standard",
      "approval_status": "approved",
      "is_active": true
    }
  ]
}
```

---

### 2.4 Filter by board type (`type`)

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?type=Premium" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK** — all owner's `Premium` boards.

---

### 2.5 Filter by active status

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?is_active=true" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?is_active=false" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK** — filtered by active/inactive.

---

### 2.6 Filter by approval status

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?approval_status=approved" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?approval_status=pending" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?approval_status=rejected" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK — no pending boards**

```json
{
  "links": { "next": null, "previous": null },
  "count": 0,
  "total_pages": 1,
  "current_page": 1,
  "results": []
}
```

---

### 2.7 Combined filters + search + ordering

```bash
curl --location "http://16.16.160.64:8000/api/billboards/my-billboards/?search=Lahore&ooh_media_type=Digital%20Billboard&is_active=true&approval_status=approved&ordering=-created_at&page=1&page_size=20" \
  --header "Authorization: Bearer MEDIA_OWNER_TOKEN"
```

**200 OK** — all conditions AND-ed; full billboard objects in `results`.

---

## 3. Wishlist — search & sort

**Endpoint:** `GET /api/billboards/wishlist/`  
**Role:** any authenticated user (typically advertiser).

### Supported query parameters

| Parameter | Type | Purpose |
|---|---|---|
| `search` | string | Search nested billboard fields |
| `ordering` | string | `created_at` or `-created_at` (wishlist add date) |
| `page`, `page_size` | int | Pagination |

### Search fields (`search` param)

| Field | Path |
|---|---|
| City | `billboard.city` |
| Description | `billboard.description` |
| Company name | `billboard.company_name` |

There are **no** django-filter field filters on wishlist (no `city=` or `ooh_media_type=` params).

---

### 3.1 Search wishlist

```bash
curl --location "http://16.16.160.64:8000/api/billboards/wishlist/?search=Lahore" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK — matches found**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 3,
      "billboard": {
        "id": 40,
        "city": "Lahore",
        "ooh_media_type": "Digital Billboard",
        "price_range": "8000",
        "latitude": 31.52,
        "longitude": 74.35,
        "is_in_wishlist": true
      },
      "created_at": "2026-06-13T12:00:00Z"
    }
  ]
}
```

**200 OK — empty wishlist or no match**

```json
{
  "links": { "next": null, "previous": null },
  "count": 0,
  "total_pages": 1,
  "current_page": 1,
  "results": []
}
```

---

### 3.2 Sort wishlist by date added

```bash
curl --location "http://16.16.160.64:8000/api/billboards/wishlist/?ordering=-created_at" \
  --header "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**200 OK** — newest saved boards first.

---

## Quick reference matrix

### Public list `GET /api/billboards/`

| Feature | Param | Example |
|---|---|---|
| Text search | `search` | `?search=Lahore` |
| Media type filter | `ooh_media_type` | `?ooh_media_type=Digital Billboard` |
| City filter | `city` | `?city=Lahore` |
| Board tier | `type` | `?type=Premium` |
| Map bounds (PostGIS) | `ne_lat`, `ne_lng`, `sw_lat`, `sw_lng` | `?ne_lat=32&ne_lng=75&sw_lat=31&sw_lng=74` |
| Radius km (PostGIS) | `lat`, `lng`, `radius` | `?lat=31.52&lng=74.35&radius=10` |
| Clustering | `cluster`, `zoom` | `?cluster=true&zoom=10&ne_lat=...` |
| Sort | `ordering` | `?ordering=-created_at` |
| Pagination | `page`, `page_size` | `?page=1&page_size=20` |

### My billboards `GET /api/billboards/my-billboards/`

| Feature | Param | Example |
|---|---|---|
| Text search | `search` | `?search=Test` |
| City filter | `city` | `?city=Lahore` |
| Media type | `ooh_media_type` | `?ooh_media_type=Static Billboard` |
| Board tier | `type` | `?type=Premium` |
| Active | `is_active` | `?is_active=true` |
| Approval | `approval_status` | `?approval_status=pending` |
| Sort | `ordering` | `?ordering=-price_range` |
| Pagination | `page`, `page_size` | `?page=1` |

### Wishlist `GET /api/billboards/wishlist/`

| Feature | Param | Example |
|---|---|---|
| Text search | `search` | `?search=Lahore` |
| Sort | `ordering` | `?ordering=-created_at` |
| Pagination | `page`, `page_size` | `?page=1` |

---

## Next.js implementation notes

### Map page (advertiser)

1. On map move/zoom, call public list with bounds + optional filters:
   ```
   GET /api/billboards/?ne_lat=...&ne_lng=...&sw_lat=...&sw_lng=...&cluster=true&zoom={zoom}&ooh_media_type=...
   ```
2. On search bar submit, add `search={query}` to the same request.
3. Render `clusters[]` — if `type === "marker"`, use `id` for preview; if `type === "cluster"`, zoom to `expansion_zoom`.
4. Pin tap → `GET /api/billboards/{id}/preview/`.

### Filter chips

| UI chip | API param | Endpoint |
|---|---|---|
| All | (omit `ooh_media_type`) | `/api/billboards/` |
| Digital | `ooh_media_type=Digital Billboard` | `/api/billboards/` |
| Static | `ooh_media_type=Static Billboard` | `/api/billboards/` |
| Near me | `lat`, `lng`, `radius` | `/api/billboards/` (PostGIS km radius, nearest first) |

### Media owner dashboard

Use `my-billboards` with tab filters:

| Tab | Params |
|---|---|
| Active | `?is_active=true&approval_status=approved` |
| Pending approval | `?approval_status=pending` |
| Inactive | `?is_active=false` |

### URL-encoding

Encode spaces in query values:

```
Digital Billboard  →  Digital%20Billboard
```

---

## Related guides

| File | Topic |
|---|---|
| `COMPLETE_API_GUIDE.md` | Full API reference |
| `BILLBOARD_PREVIEW_API_GUIDE.md` | Pin tap preview after search |
| `BILLBOARD_SPECIFICATIONS_GUIDE.md` | Digital/static specification JSON |

---

*Search and filter use DRF `SearchFilter`, `OrderingFilter`, and `BillboardFilter` with **PostGIS** geo queries (`billboards/geo_utils.py`, `billboards/filters.py`). Supabase: PostGIS 3.3.7 + GiST index on `location`.*
