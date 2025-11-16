# 🗺️ Map View API Guide

## Problem Solved

**Issue:** When displaying thousands of billboards on a map, pagination doesn't make sense. You need ALL billboards within the visible map bounds, not paginated results.

**Solution:** The API now supports **map bounds filtering** which automatically disables pagination and returns all billboards within the visible map area.

---

## 🎯 Two Use Cases

### 1. **Map View** (No Pagination)
- Use when displaying billboards on a map
- Pass map bounds (`ne_lat`, `ne_lng`, `sw_lat`, `sw_lng`)
- Returns **ALL** billboards in the visible area (no pagination)
- Perfect for map markers

### 2. **List View** (With Pagination)
- Use when displaying billboards in a list/grid
- Don't pass map bounds
- Returns paginated results (20 per page by default)
- Perfect for scrollable lists

---

## 📍 Map Bounds Filtering

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ne_lat` | number | Northeast latitude (top-right corner) | `31.5497` |
| `ne_lng` | number | Northeast longitude (top-right corner) | `74.3436` |
| `sw_lat` | number | Southwest latitude (bottom-left corner) | `31.4500` |
| `sw_lng` | number | Southwest longitude (bottom-left corner) | `74.2500` |

### How to Get Map Bounds

**React Native (Expo Maps / react-native-maps):**
```javascript
import MapView from 'react-native-maps';

const MapScreen = () => {
  const [mapBounds, setMapBounds] = useState(null);

  const handleRegionChangeComplete = (region) => {
    // Calculate bounds from region
    const ne_lat = region.latitude + (region.latitudeDelta / 2);
    const ne_lng = region.longitude + (region.longitudeDelta / 2);
    const sw_lat = region.latitude - (region.latitudeDelta / 2);
    const sw_lng = region.longitude - (region.longitudeDelta / 2);
    
    setMapBounds({ ne_lat, ne_lng, sw_lat, sw_lng });
  };

  return (
    <MapView
      onRegionChangeComplete={handleRegionChangeComplete}
      // ... other props
    />
  );
};
```

**Google Maps (Web/React):**
```javascript
const handleBoundsChanged = () => {
  const bounds = map.getBounds();
  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();
  
  const mapBounds = {
    ne_lat: ne.lat(),
    ne_lng: ne.lng(),
    sw_lat: sw.lat(),
    sw_lng: sw.lng()
  };
};
```

---

## 🔌 API Endpoints

### Map View (No Pagination)

**Request:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/?ne_lat=31.5497&ne_lng=74.3436&sw_lat=31.4500&sw_lng=74.2500" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "latitude": 31.5000,
      "longitude": 74.3000,
      "city": "Lahore",
      ...
    },
    // ... all billboards in bounds (no pagination)
  ]
}
```

### List View (With Pagination)

**Request:**
```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/?page=1&page_size=20" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "links": {
    "next": "http://44.200.108.209:8000/api/billboards/?page=2",
    "previous": null
  },
  "count": 1000,
  "total_pages": 50,
  "current_page": 1,
  "results": [
    // ... 20 billboards per page
  ]
}
```

---

## 🚀 Frontend Implementation

### React Native Example

```javascript
import { useState, useEffect } from 'react';
import MapView, { Marker } from 'react-native-maps';

const BillboardMapScreen = () => {
  const [billboards, setBillboards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mapRegion, setMapRegion] = useState({
    latitude: 31.5497,
    longitude: 74.3436,
    latitudeDelta: 0.1,
    longitudeDelta: 0.1,
  });

  const fetchBillboardsInBounds = async (region) => {
    setLoading(true);
    try {
      // Calculate bounds
      const ne_lat = region.latitude + (region.latitudeDelta / 2);
      const ne_lng = region.longitude + (region.longitudeDelta / 2);
      const sw_lat = region.latitude - (region.latitudeDelta / 2);
      const sw_lng = region.longitude - (region.longitudeDelta / 2);

      // Fetch billboards in bounds
      const response = await fetch(
        `http://44.200.108.209:8000/api/billboards/?ne_lat=${ne_lat}&ne_lng=${ne_lng}&sw_lat=${sw_lat}&sw_lng=${sw_lng}`
      );
      const data = await response.json();
      setBillboards(data.results);
    } catch (error) {
      console.error('Error fetching billboards:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegionChangeComplete = (region) => {
    setMapRegion(region);
    fetchBillboardsInBounds(region);
  };

  useEffect(() => {
    fetchBillboardsInBounds(mapRegion);
  }, []);

  return (
    <MapView
      region={mapRegion}
      onRegionChangeComplete={handleRegionChangeComplete}
      style={{ flex: 1 }}
    >
      {billboards.map((billboard) => (
        <Marker
          key={billboard.id}
          coordinate={{
            latitude: billboard.latitude,
            longitude: billboard.longitude,
          }}
          title={billboard.company_name}
        />
      ))}
    </MapView>
  );
};
```

### Debouncing (Recommended)

To avoid too many API calls while the user is panning the map:

```javascript
import { debounce } from 'lodash';

const debouncedFetch = debounce((region) => {
  fetchBillboardsInBounds(region);
}, 500); // Wait 500ms after user stops panning

const handleRegionChangeComplete = (region) => {
  setMapRegion(region);
  debouncedFetch(region);
};
```

---

## 🎨 Combined Filters

You can combine map bounds with other filters:

```bash
# Map bounds + Media type filter
curl -X GET "http://44.200.108.209:8000/api/billboards/?ne_lat=31.5497&ne_lng=74.3436&sw_lat=31.4500&sw_lng=74.2500&ooh_media_type=Digital%20Billboard"
```

---

## ⚡ Performance Tips

1. **Use Map Bounds**: Always use map bounds for map views (not radius search)
2. **Debounce Requests**: Wait 300-500ms after map movement stops before fetching
3. **Limit Initial Load**: Load billboards only when map is ready
4. **Cache Results**: Cache billboards for recently viewed areas
5. **Optimize Marker Rendering**: Use clustering for dense areas (e.g., `react-native-map-clustering`)

---

## 📊 Response Comparison

| Feature | Map View (with bounds) | List View (no bounds) |
|---------|------------------------|----------------------|
| **Pagination** | ❌ Disabled | ✅ Enabled |
| **Response Format** | `{count, results}` | `{count, links, total_pages, current_page, results}` |
| **Use Case** | Map markers | Scrollable list |
| **Max Results** | All in bounds | 20 per page (configurable) |

---

## 🔍 Fallback: Radius Search

If you prefer radius-based search (older method):

```bash
curl -X GET "http://44.200.108.209:8000/api/billboards/?lat=31.5497&lng=74.3436&radius=10"
```

**Note:** Map bounds filtering is preferred for map views as it's more accurate and efficient.

---

## ✅ Summary

- **Map View**: Use `ne_lat`, `ne_lng`, `sw_lat`, `sw_lng` → No pagination, all results
- **List View**: Don't use map bounds → Pagination enabled, 20 per page
- **Performance**: Debounce map movements, use bounds filtering
- **Best Practice**: Always use map bounds for map views, not radius search

