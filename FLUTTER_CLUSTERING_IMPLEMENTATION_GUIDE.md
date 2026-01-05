# 🗺️ Flutter Map Clustering Implementation Guide

## 📋 Overview

This guide explains how to implement backend clustering for billboards on a Flutter map. The backend now supports **grid-based clustering** (similar to Uber/Airbnb) that groups nearby billboards into clusters based on zoom level.

### Key Features:
- ✅ **Grid-based clustering** - Groups nearby billboards automatically
- ✅ **Zoom-aware** - Cluster size adapts to map zoom level
- ✅ **Performance optimized** - Reduces data transfer for thousands of billboards
- ✅ **Backward compatible** - Works with or without clustering

---

## 🔗 API Endpoint

```
GET /api/billboards/
```

**Base URL:** `http://localhost:8000` (or your server URL)

---

## 📤 cURL Commands

### 1. With Clustering Enabled (Recommended for Map Views)

```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2&cluster=true&zoom=10" \
  -H "Content-Type: application/json"
```

### 2. Without Clustering (Individual Markers)

```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2" \
  -H "Content-Type: application/json"
```

### 3. With Clustering + Media Type Filter

```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2&cluster=true&zoom=12&ooh_media_type=Digital%20Billboard" \
  -H "Content-Type: application/json"
```

### 4. With Clustering + Search

```bash
curl -X GET "http://localhost:8000/api/billboards/?ne_lat=31.5&ne_lng=74.3&sw_lat=31.4&sw_lng=74.2&cluster=true&zoom=10&search=Lahore" \
  -H "Content-Type: application/json"
```

---

## 📥 Expected Responses

### Response 1: With Clustering Enabled

```json
{
  "count": 1500,
  "clustered_count": 45,
  "clustering_enabled": true,
  "zoom_level": 10.0,
  "clusters": [
    {
      "type": "cluster",
      "latitude": 31.4591,
      "longitude": 74.2429,
      "count": 25,
      "bounds": {
        "ne_lat": 31.4600,
        "ne_lng": 74.2450,
        "sw_lat": 31.4580,
        "sw_lng": 74.2400
      },
      "grid_lat": 31.4,
      "grid_lng": 74.2
    },
    {
      "type": "cluster",
      "latitude": 31.4700,
      "longitude": 74.2500,
      "count": 12,
      "bounds": {
        "ne_lat": 31.4710,
        "ne_lng": 74.2510,
        "sw_lat": 31.4690,
        "sw_lng": 74.2490
      },
      "grid_lat": 31.4,
      "grid_lng": 74.2
    },
    {
      "type": "marker",
      "id": 123,
      "latitude": 31.4800,
      "longitude": 74.2600,
      "data": {
        "id": 123,
        "city": "Lahore",
        "description": "Premium digital billboard",
        "latitude": 31.4800,
        "longitude": 74.2600,
        "company_name": "ABC Media",
        "ooh_media_type": "Digital Billboard",
        "price_range": "50000-100000",
        "images": ["http://localhost:8000/media/billboards/billboard1.jpg"],
        "views": 150,
        "leads": 12,
        "is_active": true,
        "address": "Main Boulevard, Lahore"
      }
    }
  ]
}
```

### Response 2: Without Clustering

```json
{
  "count": 1500,
  "clustering_enabled": false,
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
      "approval_status_display": "Approved"
    }
  ]
}
```

---

## 📊 Response Fields Explanation

### Clustered Response Fields:

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of billboards in the visible area |
| `clustered_count` | integer | Number of clusters/markers returned |
| `clustering_enabled` | boolean | Whether clustering was applied |
| `zoom_level` | float | Zoom level used for clustering |
| `clusters` | array | Array of clusters and individual markers |

### Cluster Object Fields:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `"cluster"` or `"marker"` |
| `latitude` | float | Center latitude (for cluster) or billboard latitude |
| `longitude` | float | Center longitude (for cluster) or billboard longitude |
| `count` | integer | Number of billboards in cluster (only for clusters) |
| `bounds` | object | Bounding box of cluster (only for clusters) |
| `id` | integer | Billboard ID (only for individual markers) |
| `data` | object | Full billboard data (only for individual markers) |

---

## 🚀 Flutter Implementation

### Step 1: Add Dependencies

Add to `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  google_maps_flutter: ^2.5.0
  # OR
  flutter_map: ^6.0.0
  http: ^1.1.0
  provider: ^6.1.0  # For state management (optional)
```

### Step 2: Create API Service

Create `lib/services/billboard_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class BillboardService {
  final String baseUrl;
  
  BillboardService({this.baseUrl = 'http://localhost:8000'});
  
  /// Fetch billboards with clustering support
  Future<Map<String, dynamic>> fetchBillboards({
    required double neLat,
    required double neLng,
    required double swLat,
    required double swLng,
    bool cluster = true,
    double zoom = 10.0,
    String? mediaType,
    String? search,
  }) async {
    try {
      // Build query parameters
      final queryParams = {
        'ne_lat': neLat.toString(),
        'ne_lng': neLng.toString(),
        'sw_lat': swLat.toString(),
        'sw_lng': swLng.toString(),
        'cluster': cluster.toString(),
        'zoom': zoom.toString(),
      };
      
      // Add optional filters
      if (mediaType != null && mediaType.isNotEmpty) {
        queryParams['ooh_media_type'] = mediaType;
      }
      if (search != null && search.isNotEmpty) {
        queryParams['search'] = search;
      }
      
      // Build URL
      final uri = Uri.parse('$baseUrl/api/billboards/').replace(
        queryParameters: queryParams,
      );
      
      // Make request
      final response = await http.get(
        uri,
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load billboards: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching billboards: $e');
    }
  }
}
```

### Step 3: Create Map Screen with Clustering

Create `lib/screens/billboard_map_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../services/billboard_service.dart';
import 'dart:async';

class BillboardMapScreen extends StatefulWidget {
  @override
  _BillboardMapScreenState createState() => _BillboardMapScreenState();
}

class _BillboardMapScreenState extends State<BillboardMapScreen> {
  GoogleMapController? _mapController;
  final BillboardService _billboardService = BillboardService();
  Set<Marker> _markers = {};
  bool _isLoading = false;
  Timer? _debounceTimer;
  
  // Map bounds
  double? _neLat, _neLng, _swLat, _swLng;
  double _currentZoom = 10.0;
  
  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }
  
  /// Handle map camera movement with debouncing
  void _onCameraMove(CameraPosition position) {
    _currentZoom = position.zoom;
    
    // Cancel previous timer
    _debounceTimer?.cancel();
    
    // Set new timer (wait 500ms after user stops moving)
    _debounceTimer = Timer(Duration(milliseconds: 500), () {
      _updateMapBounds(position);
      _fetchBillboards();
    });
  }
  
  /// Calculate map bounds from camera position
  void _updateMapBounds(CameraPosition position) {
    // Calculate visible region bounds
    // Note: This is approximate. For exact bounds, use mapController.getVisibleRegion()
    final latDelta = position.target.latitude * 0.01; // Approximate
    final lngDelta = position.target.longitude * 0.01;
    
    setState(() {
      _neLat = position.target.latitude + latDelta;
      _neLng = position.target.longitude + lngDelta;
      _swLat = position.target.latitude - latDelta;
      _swLng = position.target.longitude - lngDelta;
    });
  }
  
  /// Fetch billboards from API
  Future<void> _fetchBillboards() async {
    if (_neLat == null || _neLng == null || _swLat == null || _swLng == null) {
      return;
    }
    
    setState(() {
      _isLoading = true;
    });
    
    try {
      // Determine if clustering should be used
      // Use clustering for zoom < 12 or when expecting many markers
      final useClustering = _currentZoom < 12;
      
      final data = await _billboardService.fetchBillboards(
        neLat: _neLat!,
        neLng: _neLng!,
        swLat: _swLat!,
        swLng: _swLng!,
        cluster: useClustering,
        zoom: _currentZoom,
      );
      
      // Process response
      if (data['clustering_enabled'] == true) {
        _processClusteredResponse(data);
      } else {
        _processIndividualMarkers(data);
      }
    } catch (e) {
      print('Error fetching billboards: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading billboards: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  /// Process clustered response
  void _processClusteredResponse(Map<String, dynamic> data) {
    final clusters = data['clusters'] as List;
    final Set<Marker> newMarkers = {};
    
    for (var item in clusters) {
      if (item['type'] == 'cluster') {
        // Create cluster marker
        final marker = Marker(
          markerId: MarkerId('cluster_${item['grid_lat']}_${item['grid_lng']}'),
          position: LatLng(
            item['latitude'] as double,
            item['longitude'] as double,
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
          infoWindow: InfoWindow(
            title: '${item['count']} Billboards',
            snippet: 'Tap to zoom in',
          ),
          onTap: () {
            // Zoom in when cluster is tapped
            _zoomToCluster(item);
          },
        );
        newMarkers.add(marker);
      } else if (item['type'] == 'marker') {
        // Create individual marker
        final billboard = item['data'] as Map<String, dynamic>;
        final marker = Marker(
          markerId: MarkerId('billboard_${billboard['id']}'),
          position: LatLng(
            item['latitude'] as double,
            item['longitude'] as double,
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          infoWindow: InfoWindow(
            title: billboard['company_name'] ?? 'Billboard',
            snippet: billboard['address'] ?? '',
          ),
          onTap: () {
            // Show billboard details
            _showBillboardDetails(billboard);
          },
        );
        newMarkers.add(marker);
      }
    }
    
    setState(() {
      _markers = newMarkers;
    });
  }
  
  /// Process individual markers response
  void _processIndividualMarkers(Map<String, dynamic> data) {
    final results = data['results'] as List;
    final Set<Marker> newMarkers = {};
    
    for (var billboard in results) {
      final marker = Marker(
        markerId: MarkerId('billboard_${billboard['id']}'),
        position: LatLng(
          billboard['latitude'] as double,
          billboard['longitude'] as double,
        ),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
        infoWindow: InfoWindow(
          title: billboard['company_name'] ?? 'Billboard',
          snippet: billboard['address'] ?? '',
        ),
        onTap: () {
          _showBillboardDetails(billboard);
        },
      );
      newMarkers.add(marker);
    }
    
    setState(() {
      _markers = newMarkers;
    });
  }
  
  /// Zoom to cluster bounds
  void _zoomToCluster(Map<String, dynamic> cluster) {
    final bounds = cluster['bounds'] as Map<String, dynamic>;
    _mapController?.animateCamera(
      CameraUpdate.newLatLngBounds(
        LatLngBounds(
          southwest: LatLng(
            bounds['sw_lat'] as double,
            bounds['sw_lng'] as double,
          ),
          northeast: LatLng(
            bounds['ne_lat'] as double,
            bounds['ne_lng'] as double,
          ),
        ),
        100.0, // padding
      ),
    );
  }
  
  /// Show billboard details
  void _showBillboardDetails(Map<String, dynamic> billboard) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(billboard['company_name'] ?? 'Billboard'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('City: ${billboard['city'] ?? 'N/A'}'),
            Text('Type: ${billboard['ooh_media_type'] ?? 'N/A'}'),
            Text('Price: ${billboard['price_range'] ?? 'N/A'}'),
            Text('Views: ${billboard['views'] ?? 0}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Billboards Map'),
      ),
      body: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: LatLng(31.5497, 74.3436), // Default location (Lahore)
              zoom: 10.0,
            ),
            markers: _markers,
            onMapCreated: (GoogleMapController controller) {
              _mapController = controller;
              // Fetch initial billboards
              _updateMapBounds(CameraPosition(
                target: LatLng(31.5497, 74.3436),
                zoom: 10.0,
              ));
              _fetchBillboards();
            },
            onCameraMove: _onCameraMove,
            onCameraIdle: () {
              // Fetch when camera stops moving
              if (_mapController != null) {
                _mapController!.getVisibleRegion().then((bounds) {
                  setState(() {
                    _neLat = bounds.northeast.latitude;
                    _neLng = bounds.northeast.longitude;
                    _swLat = bounds.southwest.latitude;
                    _swLng = bounds.southwest.longitude;
                  });
                  _fetchBillboards();
                });
              }
            },
          ),
          if (_isLoading)
            Center(
              child: CircularProgressIndicator(),
            ),
        ],
      ),
    );
  }
}
```

### Step 4: Advanced - Custom Cluster Marker Widget

For better cluster visualization, create custom cluster markers:

```dart
import 'package:flutter/material.dart';
import 'dart:ui' as ui;

/// Create custom cluster marker icon
Future<BitmapDescriptor> createClusterIcon(int count) async {
  final recorder = ui.PictureRecorder();
  final canvas = Canvas(recorder);
  final size = Size(50, 50);
  
  // Draw circle background
  final paint = Paint()
    ..color = Colors.blue
    ..style = PaintingStyle.fill;
  canvas.drawCircle(
    Offset(size.width / 2, size.height / 2),
    size.width / 2,
    paint,
  );
  
  // Draw count text
  final textPainter = TextPainter(
    text: TextSpan(
      text: count.toString(),
      style: TextStyle(
        color: Colors.white,
        fontSize: 16,
        fontWeight: FontWeight.bold,
      ),
    ),
    textDirection: TextDirection.ltr,
  );
  textPainter.layout();
  textPainter.paint(
    canvas,
    Offset(
      (size.width - textPainter.width) / 2,
      (size.height - textPainter.height) / 2,
    ),
  );
  
  final picture = recorder.endRecording();
  final image = await picture.toImage(size.width.toInt(), size.height.toInt());
  final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
  
  return BitmapDescriptor.fromBytes(bytes!.buffer.asUint8List());
}
```

Update `_processClusteredResponse` to use custom icons:

```dart
// In _processClusteredResponse method, replace cluster marker creation:
final clusterIcon = await createClusterIcon(item['count'] as int);
final marker = Marker(
  markerId: MarkerId('cluster_${item['grid_lat']}_${item['grid_lng']}'),
  position: LatLng(
    item['latitude'] as double,
    item['longitude'] as double,
  ),
  icon: clusterIcon, // Use custom icon
  // ... rest of the code
);
```

---

## 🎯 Best Practices

### 1. Debouncing
Always debounce map camera movements to avoid excessive API calls:
```dart
Timer? _debounceTimer;
_debounceTimer?.cancel();
_debounceTimer = Timer(Duration(milliseconds: 500), () {
  _fetchBillboards();
});
```

### 2. Zoom-Based Clustering
Use clustering at low zoom levels, individual markers at high zoom:
```dart
final useClustering = _currentZoom < 12;
```

### 3. Error Handling
Always handle network errors gracefully:
```dart
try {
  final data = await _billboardService.fetchBillboards(...);
} catch (e) {
  // Show user-friendly error message
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('Error loading billboards')),
  );
}
```

### 4. Loading States
Show loading indicators during API calls:
```dart
if (_isLoading)
  Center(child: CircularProgressIndicator())
```

### 5. Memory Management
Clear old markers before adding new ones:
```dart
setState(() {
  _markers.clear();
  _markers = newMarkers;
});
```

---

## 📱 Complete Example Usage

```dart
// In your main.dart or route
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => BillboardMapScreen(),
  ),
);
```

---

## 🔧 Configuration Options

### Clustering Thresholds

The backend automatically adjusts cluster size based on zoom:

| Zoom Level | Grid Size | Use Case |
|------------|-----------|----------|
| 1-5 | ~1.0° | Country/Region view |
| 6-10 | ~0.1° | City view |
| 11-15 | ~0.01° | Neighborhood view |
| 16+ | ~0.001° | Street view |

### Recommended Settings

- **Low Zoom (< 12)**: Always use clustering (`cluster=true`)
- **High Zoom (≥ 12)**: Use clustering if count > 100, otherwise individual markers
- **Debounce Time**: 300-500ms after map movement stops

---

## 🐛 Troubleshooting

### Issue: Too many API calls
**Solution**: Increase debounce time or check if bounds actually changed

### Issue: Clusters not showing
**Solution**: Check if `clustering_enabled: true` in response, verify zoom level

### Issue: Performance issues
**Solution**: Use clustering at low zoom, limit visible region, cache results

---

## ✅ Testing Checklist

- [ ] Map loads with initial billboards
- [ ] Clustering works at low zoom levels
- [ ] Individual markers show at high zoom
- [ ] Debouncing prevents excessive API calls
- [ ] Error handling works for network failures
- [ ] Cluster tap zooms in correctly
- [ ] Individual marker tap shows details
- [ ] Loading indicators appear during fetch
- [ ] Markers update when map bounds change

---

## 📚 Additional Resources

- Google Maps Flutter: https://pub.dev/packages/google_maps_flutter
- Flutter Map: https://pub.dev/packages/flutter_map
- HTTP Package: https://pub.dev/packages/http

---

## 🎉 Summary

1. **API Endpoint**: `GET /api/billboards/` with `cluster=true&zoom=X`
2. **Response Format**: Clusters array with `type: "cluster"` or `type: "marker"`
3. **Implementation**: Use debouncing, zoom-based clustering, custom cluster icons
4. **Best Practices**: Error handling, loading states, memory management

This implementation will efficiently handle thousands of billboards on your Flutter map! 🚀

