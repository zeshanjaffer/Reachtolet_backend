# 📋 Public Billboards GET API - Complete Guide

## 🔗 API Endpoint
```
GET /api/billboards/
```

## 🔑 Key Details
- **Permission**: Public (No authentication required - `AllowAny`)
- **Returns**: Only **approved** and **active** billboards
- **Pagination**: Default 20 items per page (max 100)
- **Filtering**: Supports media type, location (radius/bounds), search, and ordering

---

## 📤 cURL Command

### Basic Request (Get All Public Billboards)
```bash
curl -X GET "http://localhost:8000/api/billboards/" \
  -H "Content-Type: application/json"
```

### With Pagination
```bash
curl -X GET "http://localhost:8000/api/billboards/?page=1&page_size=20" \
  -H "Content-Type: application/json"
```

### With Filters (Media Type)
```bash
curl -X GET "http://localhost:8000/api/billboards/?ooh_media_type=Digital%20Billboard" \
  -H "Content-Type: application/json"
```

### With Location Radius Filter
```bash
curl -X GET "http://localhost:8000/api/billboards/?lat=31.4591&lng=74.2429&radius=10" \
  -H "Content-Type: application/json"
```

### With Map Bounds (No Pagination - Returns All in Bounds)
```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2" \
  -H "Content-Type: application/json"
```

### With Search
```bash
curl -X GET "http://localhost:8000/api/billboards/?search=Lahore" \
  -H "Content-Type: application/json"
```

### With Ordering
```bash
curl -X GET "http://localhost:8000/api/billboards/?ordering=-created_at" \
  -H "Content-Type: application/json"
```

### Combined Filters
```bash
curl -X GET "http://localhost:8000/api/billboards/?ooh_media_type=Digital%20Billboard&search=Lahore&ordering=-views&page=1&page_size=10" \
  -H "Content-Type: application/json"
```

---

## 📥 Complete Response Structure

### Paginated Response (Default)
```json
{
  "links": {
    "next": "http://localhost:8000/api/billboards/?page=2",
    "previous": null
  },
  "count": 45,
  "total_pages": 3,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      "description": "Premium digital billboard located at main highway",
      "number_of_boards": "2",
      "average_daily_views": "50000",
      "traffic_direction": "North-South",
      "road_position": "Right side",
      "road_name": "Main Boulevard",
      "exposure_time": "24/7",
      "price_range": "50000-100000",
      "display_height": "10",
      "display_width": "20",
      "advertiser_phone": "+92-300-1234567",
      "advertiser_whatsapp": "+92-300-1234567",
      "company_name": "ABC Media",
      "company_website": "https://www.abcmedia.com",
      "ooh_media_type": "Digital Billboard",
      "ooh_media_id": "DB-001",
      "type": "Premium",
      "images": [
        "http://localhost:8000/media/billboards/billboard1.jpg",
        "http://localhost:8000/media/billboards/billboard2.jpg"
      ],
      "unavailable_dates": ["2025-12-25", "2025-12-31"],
      "latitude": 31.4591,
      "longitude": 74.2429,
      "views": 150,
      "leads": 12,
      "is_active": true,
      "address": "Main Boulevard, Lahore",
      "generator_backup": true,
      "created_at": "2025-11-15T10:30:00Z",
      "user_name": "John Doe",
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "approved_at": "2025-11-16T09:15:00Z",
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": "admin",
      "rejected_by_username": null
    },
    {
      "id": 2,
      "city": "Karachi",
      "description": "Static billboard at busy intersection",
      "number_of_boards": "1",
      "average_daily_views": "30000",
      "traffic_direction": "East-West",
      "road_position": "Left side",
      "road_name": "Shahrah-e-Faisal",
      "exposure_time": "24/7",
      "price_range": "30000-50000",
      "display_height": "8",
      "display_width": "15",
      "advertiser_phone": "+92-300-9876543",
      "advertiser_whatsapp": "+92-300-9876543",
      "company_name": "XYZ Advertising",
      "company_website": "https://www.xyzadvertising.com",
      "ooh_media_type": "Static Billboard",
      "ooh_media_id": "SB-002",
      "type": "Standard",
      "images": [
        "http://localhost:8000/media/billboards/billboard3.jpg"
      ],
      "unavailable_dates": [],
      "latitude": 24.8607,
      "longitude": 67.0011,
      "views": 89,
      "leads": 5,
      "is_active": true,
      "address": "Shahrah-e-Faisal, Karachi",
      "generator_backup": false,
      "created_at": "2025-11-14T14:20:00Z",
      "user_name": "Jane Smith",
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "approved_at": "2025-11-15T08:30:00Z",
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": "admin",
      "rejected_by_username": null
    }
  ]
}
```

### Non-Paginated Response (When Map Bounds Provided)
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "city": "Lahore",
      "description": "Premium digital billboard located at main highway",
      "number_of_boards": "2",
      "average_daily_views": "50000",
      "traffic_direction": "North-South",
      "road_position": "Right side",
      "road_name": "Main Boulevard",
      "exposure_time": "24/7",
      "price_range": "50000-100000",
      "display_height": "10",
      "display_width": "20",
      "advertiser_phone": "+92-300-1234567",
      "advertiser_whatsapp": "+92-300-1234567",
      "company_name": "ABC Media",
      "company_website": "https://www.abcmedia.com",
      "ooh_media_type": "Digital Billboard",
      "ooh_media_id": "DB-001",
      "type": "Premium",
      "images": [
        "http://localhost:8000/media/billboards/billboard1.jpg",
        "http://localhost:8000/media/billboards/billboard2.jpg"
      ],
      "unavailable_dates": ["2025-12-25", "2025-12-31"],
      "latitude": 31.4591,
      "longitude": 74.2429,
      "views": 150,
      "leads": 12,
      "is_active": true,
      "address": "Main Boulevard, Lahore",
      "generator_backup": true,
      "created_at": "2025-11-15T10:30:00Z",
      "user_name": "John Doe",
      "approval_status": "approved",
      "approval_status_display": "Approved",
      "approved_at": "2025-11-16T09:15:00Z",
      "rejected_at": null,
      "rejection_reason": null,
      "approved_by_username": "admin",
      "rejected_by_username": null
    }
  ]
}
```

---

## 🔍 Available Query Parameters

### Pagination
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page (max 100) | `?page_size=20` |

### Filtering
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ooh_media_type` | string | Filter by media type (exact match, case-insensitive) | `?ooh_media_type=Digital Billboard` |
| `lat` | number | Center latitude for radius search | `?lat=31.4591` |
| `lng` | number | Center longitude for radius search | `?lng=74.2429` |
| `radius` | number | Radius in kilometers | `?radius=10` |
| `ne_lat` | number | Northeast latitude (map bounds) | `?ne_lat=31.5` |
| `ne_lng` | number | Northeast longitude (map bounds) | `?ne_lng=74.3` |
| `sw_lat` | number | Southwest latitude (map bounds) | `?sw_lat=31.4` |
| `sw_lng` | number | Southwest longitude (map bounds) | `?sw_lng=74.2` |

### Search
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in: city, description, company_name, road_name | `?search=Lahore` |

### Ordering
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ordering` | string | Order by: created_at, price_range, city, views | `?ordering=-created_at` (desc) or `?ordering=created_at` (asc) |

---

## 📊 Response Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Billboard unique identifier |
| `city` | string | City where billboard is located |
| `description` | string | Billboard description |
| `number_of_boards` | string | Number of boards at location |
| `average_daily_views` | string | Average daily view count |
| `traffic_direction` | string | Traffic direction |
| `road_position` | string | Position on road |
| `road_name` | string | Name of the road |
| `exposure_time` | string | Exposure time (e.g., "24/7") |
| `price_range` | string | Price range for advertising |
| `display_height` | string | Display height |
| `display_width` | string | Display width |
| `advertiser_phone` | string | Contact phone number |
| `advertiser_whatsapp` | string | WhatsApp contact |
| `company_name` | string | Company name |
| `company_website` | string | Company website URL |
| `ooh_media_type` | string | Type of media (Digital Billboard, Static Billboard, LED Display, Transit Media) |
| `ooh_media_id` | string | Media ID |
| `type` | string | Billboard type (Premium, Standard, etc.) |
| `images` | array | Array of image URLs |
| `unavailable_dates` | array | Array of unavailable dates (YYYY-MM-DD format) |
| `latitude` | float | Latitude coordinate |
| `longitude` | float | Longitude coordinate |
| `views` | integer | Total view count |
| `leads` | integer | Total lead count |
| `is_active` | boolean | Whether billboard is active |
| `address` | string | Physical address |
| `generator_backup` | boolean | Whether generator backup is available |
| `created_at` | datetime | Creation timestamp (ISO 8601) |
| `user_name` | string | Name of the billboard owner |
| `approval_status` | string | Approval status (approved, pending, rejected) |
| `approval_status_display` | string | Human-readable approval status |
| `approved_at` | datetime | Approval timestamp (ISO 8601) |
| `rejected_at` | datetime | Rejection timestamp (ISO 8601) or null |
| `rejection_reason` | string | Rejection reason or null |
| `approved_by_username` | string | Username of approver or null |
| `rejected_by_username` | string | Username of rejector or null |

---

## 🎯 Important Notes

1. **Public Access**: No authentication required - this endpoint is publicly accessible
2. **Filtered Results**: Only returns billboards with:
   - `is_active=True`
   - `approval_status='approved'`
3. **Pagination**: 
   - Default: 20 items per page
   - Maximum: 100 items per page
   - Disabled when map bounds (`ne_lat`, `ne_lng`, `sw_lat`, `sw_lng`) are provided
4. **Media Types**: Available types include:
   - `Digital Billboard`
   - `Static Billboard`
   - `LED Display`
   - `Transit Media`
5. **Ordering**: Use `-` prefix for descending order (e.g., `-created_at`)

---

## 🧪 Testing Examples

### Example 1: Get First Page
```bash
curl -X GET "http://localhost:8000/api/billboards/?page=1" \
  -H "Content-Type: application/json"
```

### Example 2: Get Digital Billboards in Lahore
```bash
curl -X GET "http://localhost:8000/api/billboards/?ooh_media_type=Digital%20Billboard&search=Lahore" \
  -H "Content-Type: application/json"
```

### Example 3: Get Billboards Within 10km Radius
```bash
curl -X GET "http://localhost:8000/api/billboards/?lat=31.4591&lng=74.2429&radius=10" \
  -H "Content-Type: application/json"
```

### Example 4: Get Billboards in Map Viewport (No Pagination)
```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2" \
  -H "Content-Type: application/json"
```

### Example 5: Get Most Viewed Billboards
```bash
curl -X GET "http://localhost:8000/api/billboards/?ordering=-views&page_size=10" \
  -H "Content-Type: application/json"
```



