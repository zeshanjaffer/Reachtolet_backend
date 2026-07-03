# My Billboards — Flutter integration guide (POST approval tabs)

Media owners list their billboards in three tabs: **Pending**, **Approved**, **Rejected**.

- **List (tiles):** `POST /api/billboards/my-billboards/` with `approval_status` in the JSON body.
- **Detail (full screen):** `GET /api/billboards/{id}/` when the user taps a tile.

> **Breaking change:** `GET /api/billboards/my-billboards/?approval_status=...` is **removed**. It returns `405 Method Not Allowed`. Migrate all list calls to **POST**.

**Base URL:** `http://16.16.160.64:8000`

---

## 1. Screen → API map

| Flutter screen | API | When |
|----------------|-----|------|
| Pending tab | `POST /api/billboards/my-billboards/` | `approval_status: "pending"` |
| Approved tab | `POST /api/billboards/my-billboards/` | `approval_status: "approved"` |
| Rejected tab | `POST /api/billboards/my-billboards/` | `approval_status: "rejected"` |
| Billboard detail | `GET /api/billboards/{id}/` | User taps a tile |
| Pull-to-refresh | Same POST as active tab | Re-send with `page: 1` |
| Load more | Same POST | Increment `page` |

---

## 2. Authentication

Every request needs the media owner JWT:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Only users with `user_type == "media_owner"` can call my-billboards. Advertisers get **403**.

---

## 3. POST list API

### Endpoint

```
POST /api/billboards/my-billboards/
```

### Request body

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `approval_status` | **yes** | string | `"pending"`, `"approved"`, or `"rejected"` |
| `page` | no | int | Default `1` |
| `page_size` | no | int | Default `20`, max `100` |
| `search` | no | string | City, description, company, road |
| `city` | no | string | Filter by city |
| `media_type_id` | no | int | Filter by media type |
| `type` | no | string | Billboard type |
| `is_active` | no | bool | Active filter |
| `ordering` | no | string | `-created_at`, `created_at`, `price_range`, `-price_range` |

### Example — Pending tab

```bash
curl --location 'http://16.16.160.64:8000/api/billboards/my-billboards/' \
  --header 'Authorization: Bearer YOUR_TOKEN' \
  --header 'Content-Type: application/json' \
  --data '{
    "approval_status": "pending",
    "page": 1,
    "page_size": 20
  }'
```

### Example — Approved tab

```json
{
  "approval_status": "approved",
  "page": 1,
  "page_size": 20
}
```

### Example — Rejected tab

```json
{
  "approval_status": "rejected",
  "page": 1,
  "page_size": 20
}
```

### Success response — `200 OK`

```json
{
  "status_code": 200,
  "message": "Billboards fetched successfully",
  "links": {
    "next": 2,
    "previous": null
  },
  "count": 25,
  "total_pages": 2,
  "current_page": 1,
  "results": [ ]
}
```

`links.next` / `links.previous` are **page numbers** (not URLs). Send the next request with `"page": links.next`.

### Tile object fields

**All tabs**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Billboard ID — use for detail navigation |
| `city` | string | |
| `road_name` | string? | |
| `image` | string? | First image URL |
| `price` | object | `{ amount, currency, period }` |
| `display_size` | object | `{ label }` e.g. `"10 × 5 meters"` |
| `media_type_name` | string? | |
| `approval_status` | string | `pending` / `approved` / `rejected` |
| `approval_status_display` | string | `Pending` / `Approved` / `Rejected` |
| `is_active` | bool | |
| `created_at` | string | ISO datetime |

**Pending only**

| Field | Value |
|-------|-------|
| `subtitle` | `"Awaiting admin approval"` |

**Approved only**

| Field | Type |
|-------|------|
| `views` | int |
| `leads` | int |
| `approved_at` | string? |

**Rejected only**

| Field | Type |
|-------|------|
| `rejection_reason` | string |
| `rejected_at` | string? |
| `subtitle` | string? | Truncated reason for tile |

### Error responses

| HTTP | Body | Cause |
|------|------|-------|
| `400` | `{ "approval_status": ["This field is required."] }` | Missing status |
| `400` | `{ "approval_status": ["\"foo\" is not a valid choice."] }` | Invalid status |
| `401` | `{ "detail": "Authentication credentials were not provided." }` | No / bad token |
| `403` | `{ "detail": "Only media owners can access their billboards. You are registered as an advertiser." }` | Wrong role |
| `405` | `{ "detail": "GET is not supported. Use POST..." }` | Old GET call — migrate to POST |

---

## 4. Detail API (tile tap)

```
GET /api/billboards/{id}/
Authorization: Bearer <token>
```

Returns the **full** billboard (images, specs, location, availability, approval fields, etc.).

**Note:** Public detail serializer does **not** include `views` / `leads`. For the approved tab, pass `views` and `leads` from the **tile** into the detail screen, or show them only on the list card.

### Rejected detail

Read `rejection_reason` from the GET response and show it prominently (read-only — no resubmit).

### Pending detail

Show status chip **Pending** and message “Awaiting admin approval”. Billboard is **not** on the public map yet.

---

## 5. Dart models

```dart
class BillboardTilePrice {
  final String? amount;
  final String currency;
  final String period;

  factory BillboardTilePrice.fromJson(Map<String, dynamic> json) => BillboardTilePrice(
    amount: json['amount']?.toString(),
    currency: json['currency'] as String? ?? 'PKR',
    period: json['period'] as String? ?? 'per month',
  );
}

class BillboardTile {
  final int id;
  final String? city;
  final String? roadName;
  final String? image;
  final BillboardTilePrice? price;
  final String? displaySizeLabel;
  final String? mediaTypeName;
  final String approvalStatus;
  final String approvalStatusDisplay;
  final bool isActive;
  final DateTime? createdAt;
  final String? subtitle;
  final int? views;
  final int? leads;
  final DateTime? approvedAt;
  final String? rejectionReason;
  final DateTime? rejectedAt;

  factory BillboardTile.fromJson(Map<String, dynamic> json) => BillboardTile(
    id: json['id'] as int,
    city: json['city'] as String?,
    roadName: json['road_name'] as String?,
    image: json['image'] as String?,
    price: json['price'] != null
        ? BillboardTilePrice.fromJson(json['price'] as Map<String, dynamic>)
        : null,
    displaySizeLabel: (json['display_size'] as Map?)?['label'] as String?,
    mediaTypeName: json['media_type_name'] as String?,
    approvalStatus: json['approval_status'] as String,
    approvalStatusDisplay: json['approval_status_display'] as String,
    isActive: json['is_active'] as bool? ?? false,
    createdAt: json['created_at'] != null
        ? DateTime.tryParse(json['created_at'] as String)
        : null,
    subtitle: json['subtitle'] as String?,
    views: json['views'] as int?,
    leads: json['leads'] as int?,
    approvedAt: json['approved_at'] != null
        ? DateTime.tryParse(json['approved_at'] as String)
        : null,
    rejectionReason: json['rejection_reason'] as String?,
    rejectedAt: json['rejected_at'] != null
        ? DateTime.tryParse(json['rejected_at'] as String)
        : null,
  );
}

class MyBillboardsListResponse {
  final int statusCode;
  final String message;
  final int count;
  final int totalPages;
  final int currentPage;
  final int? nextPage;
  final int? previousPage;
  final List<BillboardTile> results;

  factory MyBillboardsListResponse.fromJson(Map<String, dynamic> json) {
    final links = json['links'] as Map<String, dynamic>? ?? {};
    return MyBillboardsListResponse(
      statusCode: json['status_code'] as int? ?? 200,
      message: json['message'] as String? ?? '',
      count: json['count'] as int? ?? 0,
      totalPages: json['total_pages'] as int? ?? 1,
      currentPage: json['current_page'] as int? ?? 1,
      nextPage: links['next'] as int?,
      previousPage: links['previous'] as int?,
      results: (json['results'] as List<dynamic>? ?? [])
          .map((e) => BillboardTile.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
```

---

## 6. API service (Dio example)

```dart
import 'package:dio/dio.dart';

class BillboardApi {
  BillboardApi(this._dio);
  final Dio _dio;

  Future<MyBillboardsListResponse> fetchMyBillboards({
    required String approvalStatus, // pending | approved | rejected
    int page = 1,
    int pageSize = 20,
    String? search,
  }) async {
    final response = await _dio.post(
      '/api/billboards/my-billboards/',
      data: {
        'approval_status': approvalStatus,
        'page': page,
        'page_size': pageSize,
        if (search != null && search.isNotEmpty) 'search': search,
      },
    );
    return MyBillboardsListResponse.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  Future<Map<String, dynamic>> fetchBillboardDetail(int id) async {
    final response = await _dio.get('/api/billboards/$id/');
    return response.data as Map<String, dynamic>;
  }
}
```

Ensure Dio `baseUrl` is `http://16.16.160.64:8000` and an interceptor adds `Authorization: Bearer ...`.

---

## 7. Tab screen pattern (Flutter)

```dart
enum MyBillboardTab { pending, approved, rejected }

extension on MyBillboardTab {
  String get apiStatus => switch (this) {
    MyBillboardTab.pending => 'pending',
    MyBillboardTab.approved => 'approved',
    MyBillboardTab.rejected => 'rejected',
  };
}

class MyBillboardsTabView extends StatefulWidget {
  const MyBillboardsTabView({required this.tab, super.key});
  final MyBillboardTab tab;

  @override
  State<MyBillboardsTabView> createState() => _MyBillboardsTabViewState();
}

class _MyBillboardsTabViewState extends State<MyBillboardsTabView> {
  final List<BillboardTile> _tiles = [];
  int _page = 1;
  bool _loading = false;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _load(refresh: true);
  }

  Future<void> _load({bool refresh = false}) async {
    if (_loading) return;
    if (refresh) {
      _page = 1;
      _hasMore = true;
    }
    if (!_hasMore && !refresh) return;

    setState(() => _loading = true);
    try {
      final res = await billboardApi.fetchMyBillboards(
        approvalStatus: widget.tab.apiStatus,
        page: _page,
      );
      setState(() {
        if (refresh) _tiles.clear();
        _tiles.addAll(res.results);
        _hasMore = res.nextPage != null;
        if (_hasMore) _page = res.nextPage!;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _onTileTap(BillboardTile tile) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => BillboardDetailScreen(
          billboardId: tile.id,
          tile: tile, // pass views/leads for approved tab
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () => _load(refresh: true),
      child: ListView.builder(
        itemCount: _tiles.length + (_hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _tiles.length) {
            _load();
            return const Center(child: CircularProgressIndicator());
          }
          final tile = _tiles[index];
          return BillboardTileCard(tile: tile, onTap: () => _onTileTap(tile));
        },
      ),
    );
  }
}
```

### Hub with 3 tabs

```dart
DefaultTabController(
  length: 3,
  child: Scaffold(
    appBar: AppBar(
      title: const Text('My Billboards'),
      bottom: const TabBar(tabs: [
        Tab(text: 'Pending'),
        Tab(text: 'Approved'),
        Tab(text: 'Rejected'),
      ]),
    ),
    body: const TabBarView(
      children: [
        MyBillboardsTabView(tab: MyBillboardTab.pending),
        MyBillboardsTabView(tab: MyBillboardTab.approved),
        MyBillboardsTabView(tab: MyBillboardTab.rejected),
      ],
    ),
  ),
);
```

---

## 8. UI hints per tab

### Pending tile

- Status chip: **Pending** (amber/orange)
- Subtitle: `tile.subtitle` → “Awaiting admin approval”
- Hide views/leads

### Approved tile

- Status chip: **Approved** (green)
- Show `views` and `leads` on the card
- Optional: `approved_at` as “Live since …”

### Rejected tile

- Status chip: **Rejected** (red)
- Show `rejection_reason` or `subtitle` on the card
- Detail screen: full `rejection_reason` only (read-only)

---

## 9. Push notifications (refresh tabs)

When FCM arrives after admin action:

| `notification_type` | Action |
|---------------------|--------|
| `billboard_approved` | Refresh **Approved** tab; remove from **Pending** if cached |
| `billboard_rejected` | Refresh **Rejected** tab; remove from **Pending** |

Payload `data` includes `billboard_id` and `approval_status`.

---

## 10. Migration checklist (old GET → new POST)

- [ ] Replace `GET .../my-billboards/?approval_status=pending` with **POST** + body
- [ ] Replace query-param pagination (`?page=`) with `"page"` in JSON body
- [ ] Replace query-param `search` with `"search"` in JSON body
- [ ] Parse **lightweight** `results[]` tiles (not full billboard objects)
- [ ] On tile tap, call `GET /api/billboards/{id}/` for detail
- [ ] Handle **405** if any old GET calls remain
- [ ] Use `links.next` as next **page number** for infinite scroll

---

## 11. Quick test curls

```bash
export BASE="http://16.16.160.64:8000"
export TOKEN="your_media_owner_jwt"

# Pending
curl -s -X POST "$BASE/api/billboards/my-billboards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approval_status":"pending","page":1}' | jq .

# Approved
curl -s -X POST "$BASE/api/billboards/my-billboards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approval_status":"approved","page":1}' | jq .

# Rejected
curl -s -X POST "$BASE/api/billboards/my-billboards/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approval_status":"rejected","page":1}' | jq .

# Detail
curl -s "$BASE/api/billboards/45/" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Old GET (should fail)
curl -s "$BASE/api/billboards/my-billboards/?approval_status=pending" \
  -H "Authorization: Bearer $TOKEN" | jq .
```
