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

### Step 2: Create API Service (CRASH-SAFE VERSION)

Create `lib/services/billboard_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class BillboardService {
  final String baseUrl;
  
  BillboardService({this.baseUrl = 'http://localhost:8000'});
  
  /// Fetch billboards with clustering support (CRASH-SAFE)
  /// Bounds are optional - if not provided, fetches all billboards (paginated)
  Future<Map<String, dynamic>> fetchBillboards({
    double? neLat,
    double? neLng,
    double? swLat,
    double? swLng,
    bool cluster = false,
    double zoom = 10.0,
    String? mediaType,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{};
      
      // CRASH FIX: Only add bounds if all 4 are provided
      if (neLat != null && neLng != null && swLat != null && swLng != null) {
        queryParams['ne_lat'] = neLat.toString();
        queryParams['ne_lng'] = neLng.toString();
        queryParams['sw_lat'] = swLat.toString();
        queryParams['sw_lng'] = swLng.toString();
      }
      
      // Add clustering params
      queryParams['cluster'] = cluster.toString();
      queryParams['zoom'] = zoom.toString();
      
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
      
      // Make request with timeout
      final response = await http.get(
        uri,
        headers: {'Content-Type': 'application/json'},
      ).timeout(
        Duration(seconds: 30),
        onTimeout: () {
          throw Exception('Request timeout - please check your internet connection');
        },
      );
      
      if (response.statusCode == 200) {
        final decoded = json.decode(response.body) as Map<String, dynamic>;
        return decoded;
      } else if (response.statusCode == 401) {
        throw Exception('Authentication required - please login again');
      } else {
        throw Exception('Failed to load billboards: ${response.statusCode}');
      }
    } on FormatException {
      throw Exception('Invalid response from server');
    } catch (e) {
      if (e.toString().contains('timeout')) {
        rethrow;
      }
      throw Exception('Error fetching billboards: ${e.toString()}');
    }
  }
}
```

### Step 3: Create Map Screen with Clustering (CRASH-SAFE VERSION)

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
  bool _isMapReady = false;
  Timer? _debounceTimer;
  
  // Map bounds
  double? _neLat, _neLng, _swLat, _swLng;
  double _currentZoom = 10.0;
  
  // Track last fetched bounds to avoid duplicate calls
  double? _lastNeLat, _lastNeLng, _lastSwLat, _lastSwLng;
  double? _lastZoom;
  
  @override
  void dispose() {
    _debounceTimer?.cancel();
    _mapController?.dispose();
    super.dispose();
  }
  
  /// Check if bounds changed significantly (5% threshold)
  bool _shouldFetch(double neLat, double neLng, double swLat, double swLng, double zoom) {
    // Always fetch if first time
    if (_lastNeLat == null) return true;
    
    // Fetch if zoom changed significantly (more than 1 level)
    if (_lastZoom != null && (zoom - _lastZoom!).abs() > 1.0) {
      return true;
    }
    
    // Calculate bounds size
    final latSize = neLat - swLat;
    final lngSize = neLng - swLng;
    
    // Calculate change percentage
    final latChange = ((neLat - _lastNeLat!).abs() + (swLat - _lastSwLat!).abs()) / 2;
    final lngChange = ((neLng - _lastNeLng!).abs() + (swLng - _lastSwLng!).abs()) / 2;
    
    final latThreshold = latSize * 0.05;  // 5% threshold
    final lngThreshold = lngSize * 0.05;
    
    // Fetch if bounds changed by more than 5%
    if (latChange > latThreshold || lngChange > lngThreshold) {
      return true;
    }
    
    return false;
  }
  
  /// Handle map camera movement with debouncing
  void _onCameraMove(CameraPosition position) {
    _currentZoom = position.zoom;
    
    // Cancel previous timer
    _debounceTimer?.cancel();
    
    // Set new timer (wait 500ms after user stops moving)
    _debounceTimer = Timer(Duration(milliseconds: 500), () async {
      if (!mounted || _mapController == null) return;
      
      try {
        final bounds = await _mapController!.getVisibleRegion();
        
        final neLat = bounds.northeast.latitude;
        final neLng = bounds.northeast.longitude;
        final swLat = bounds.southwest.latitude;
        final swLng = bounds.southwest.longitude;
        
        // Only fetch if bounds changed significantly
        if (_shouldFetch(neLat, neLng, swLat, swLng, _currentZoom)) {
          if (mounted) {
            setState(() {
              _neLat = neLat;
              _neLng = neLng;
              _swLat = swLat;
              _swLng = swLng;
              _lastNeLat = neLat;
              _lastNeLng = neLng;
              _lastSwLat = swLat;
              _lastSwLng = swLng;
              _lastZoom = _currentZoom;
            });
            _fetchBillboards();
          }
        }
      } catch (e) {
        print('Error getting visible region: $e');
        // Don't crash, just skip this update
      }
    });
  }
  
  /// Fetch billboards from API (CRASH-SAFE)
  Future<void> _fetchBillboards() async {
    // CRASH FIX 1: Check if bounds are available
    if (_neLat == null || _neLng == null || _swLat == null || _swLng == null) {
      print('Map bounds not ready yet, skipping fetch');
      return; // Don't crash, just return
    }
    
    // CRASH FIX 2: Check if widget is still mounted
    if (!mounted) return;
    
    setState(() {
      _isLoading = true;
    });
    
    try {
      // Determine if clustering should be used
      final useClustering = _currentZoom < 12;
      
      final data = await _billboardService.fetchBillboards(
        neLat: _neLat!,
        neLng: _neLng!,
        swLat: _swLat!,
        swLng: _swLng!,
        cluster: useClustering,
        zoom: _currentZoom,
      );
      
      // CRASH FIX 3: Check if widget is still mounted before processing
      if (!mounted) return;
      
      // Process response
      if (data['clustering_enabled'] == true) {
        _processClusteredResponse(data);
      } else {
        _processIndividualMarkers(data);
      }
    } catch (e) {
      print('Error fetching billboards: $e');
      // CRASH FIX 4: Show error but don't crash
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading billboards: ${e.toString()}'),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } finally {
      // CRASH FIX 5: Check mounted before setState
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
  
  /// Process clustered response (CRASH-SAFE)
  void _processClusteredResponse(Map<String, dynamic> data) {
    if (!mounted) return;
    
    try {
      final clusters = data['clusters'] as List?;
      if (clusters == null) return;
      
      final Set<Marker> newMarkers = {};
      
      for (var item in clusters) {
        try {
          if (item['type'] == 'cluster') {
            // Validate cluster data
            final lat = item['latitude'];
            final lng = item['longitude'];
            final count = item['count'];
            
            if (lat == null || lng == null || count == null) continue;
            
            // Create cluster marker
            final marker = Marker(
              markerId: MarkerId('cluster_${item['grid_lat']}_${item['grid_lng']}'),
              position: LatLng(
                (lat as num).toDouble(),
                (lng as num).toDouble(),
              ),
              icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
              infoWindow: InfoWindow(
                title: '$count Billboards',
                snippet: 'Tap to zoom in',
              ),
              onTap: () {
                _zoomToCluster(item);
              },
            );
            newMarkers.add(marker);
          } else if (item['type'] == 'marker') {
            // Validate marker data
            final billboard = item['data'] as Map<String, dynamic>?;
            final lat = item['latitude'];
            final lng = item['longitude'];
            
            if (billboard == null || lat == null || lng == null) continue;
            
            final billboardId = billboard['id'];
            if (billboardId == null) continue;
            
            // Create individual marker
            final marker = Marker(
              markerId: MarkerId('billboard_$billboardId'),
              position: LatLng(
                (lat as num).toDouble(),
                (lng as num).toDouble(),
              ),
              icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
              infoWindow: InfoWindow(
                title: billboard['company_name']?.toString() ?? 'Billboard',
                snippet: billboard['address']?.toString() ?? '',
              ),
              onTap: () {
                _showBillboardDetails(billboard);
              },
            );
            newMarkers.add(marker);
          }
        } catch (e) {
          print('Error processing cluster item: $e');
          continue; // Skip invalid items
        }
      }
      
      if (mounted) {
        setState(() {
          _markers = newMarkers;
        });
      }
    } catch (e) {
      print('Error processing clustered response: $e');
    }
  }
  
  /// Process individual markers response (CRASH-SAFE)
  void _processIndividualMarkers(Map<String, dynamic> data) {
    if (!mounted) return;
    
    try {
      final results = data['results'] as List?;
      if (results == null) return;
      
      final Set<Marker> newMarkers = {};
      
      for (var billboard in results) {
        try {
          final billboardMap = billboard as Map<String, dynamic>;
          final id = billboardMap['id'];
          final lat = billboardMap['latitude'];
          final lng = billboardMap['longitude'];
          
          // Validate required fields
          if (id == null || lat == null || lng == null) continue;
          
          final marker = Marker(
            markerId: MarkerId('billboard_$id'),
            position: LatLng(
              (lat as num).toDouble(),
              (lng as num).toDouble(),
            ),
            icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
            infoWindow: InfoWindow(
              title: billboardMap['company_name']?.toString() ?? 'Billboard',
              snippet: billboardMap['address']?.toString() ?? '',
            ),
            onTap: () {
              _showBillboardDetails(billboardMap);
            },
          );
          newMarkers.add(marker);
        } catch (e) {
          print('Error processing billboard: $e');
          continue; // Skip invalid billboards
        }
      }
      
      if (mounted) {
        setState(() {
          _markers = newMarkers;
        });
      }
    } catch (e) {
      print('Error processing individual markers: $e');
    }
  }
  
  /// Zoom to cluster bounds (CRASH-SAFE)
  void _zoomToCluster(Map<String, dynamic> cluster) {
    if (_mapController == null || !mounted) return;
    
    try {
      final bounds = cluster['bounds'] as Map<String, dynamic>?;
      if (bounds == null) return;
      
      final swLat = bounds['sw_lat'];
      final swLng = bounds['sw_lng'];
      final neLat = bounds['ne_lat'];
      final neLng = bounds['ne_lng'];
      
      if (swLat == null || swLng == null || neLat == null || neLng == null) return;
      
      _mapController?.animateCamera(
        CameraUpdate.newLatLngBounds(
          LatLngBounds(
            southwest: LatLng(
              (swLat as num).toDouble(),
              (swLng as num).toDouble(),
            ),
            northeast: LatLng(
              (neLat as num).toDouble(),
              (neLng as num).toDouble(),
            ),
          ),
          100.0, // padding
        ),
      );
    } catch (e) {
      print('Error zooming to cluster: $e');
    }
  }
  
  /// Show billboard details (CRASH-SAFE)
  void _showBillboardDetails(Map<String, dynamic> billboard) {
    if (!mounted) return;
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(billboard['company_name']?.toString() ?? 'Billboard'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('City: ${billboard['city']?.toString() ?? 'N/A'}'),
              SizedBox(height: 8),
              Text('Type: ${billboard['ooh_media_type']?.toString() ?? 'N/A'}'),
              SizedBox(height: 8),
              Text('Price: ${billboard['price_range']?.toString() ?? 'N/A'}'),
              SizedBox(height: 8),
              Text('Views: ${billboard['views']?.toString() ?? '0'}'),
            ],
          ),
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
            onMapCreated: (GoogleMapController controller) async {
              _mapController = controller;
              
              // CRASH FIX: Wait for map to fully initialize
              await Future.delayed(Duration(milliseconds: 300));
              
              if (!mounted || _mapController == null) return;
              
              try {
                // CRASH FIX: Get actual visible region instead of approximate
                final bounds = await _mapController!.getVisibleRegion();
                
                if (mounted) {
                  setState(() {
                    _neLat = bounds.northeast.latitude;
                    _neLng = bounds.northeast.longitude;
                    _swLat = bounds.southwest.latitude;
                    _swLng = bounds.southwest.longitude;
                    _isMapReady = true;
                  });
                  _fetchBillboards();
                }
              } catch (e) {
                print('Error getting initial map bounds: $e');
                // Fallback: use default bounds
                if (mounted) {
                  setState(() {
                    _neLat = 31.5497 + 0.1;
                    _neLng = 74.3436 + 0.1;
                    _swLat = 31.5497 - 0.1;
                    _swLng = 74.3436 - 0.1;
                    _isMapReady = true;
                  });
                  _fetchBillboards();
                }
              }
            },
            onCameraMove: _onCameraMove,
            onCameraIdle: () async {
              // CRASH FIX: Fetch when camera stops moving (with error handling)
              if (_mapController != null && mounted) {
                try {
                  final bounds = await _mapController!.getVisibleRegion();
                  
                  if (mounted) {
                    final neLat = bounds.northeast.latitude;
                    final neLng = bounds.northeast.longitude;
                    final swLat = bounds.southwest.latitude;
                    final swLng = bounds.southwest.longitude;
                    
                    // Only fetch if bounds changed significantly
                    if (_shouldFetch(neLat, neLng, swLat, swLng, _currentZoom)) {
                      setState(() {
                        _neLat = neLat;
                        _neLng = neLng;
                        _swLat = swLat;
                        _swLng = swLng;
                        _lastNeLat = neLat;
                        _lastNeLng = neLng;
                        _lastSwLat = swLat;
                        _lastSwLng = swLng;
                        _lastZoom = _currentZoom;
                      });
                      _fetchBillboards();
                    }
                  }
                } catch (e) {
                  print('Error getting visible region on idle: $e');
                  // Don't crash, just skip this update
                }
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

### Issue: App crashes on startup
**Solution**: 
- Ensure map controller is initialized before calling `getVisibleRegion()`
- Add null checks for all bounds parameters
- Use try-catch around all map operations
- Check if widget is mounted before setState

### Issue: Too many API calls
**Solution**: Increase debounce time or check if bounds actually changed

### Issue: Clusters not showing
**Solution**: Check if `clustering_enabled: true` in response, verify zoom level

### Issue: Performance issues
**Solution**: Use clustering at low zoom, limit visible region, cache results

### Issue: "Map bounds not ready" error
**Solution**: 
- Wait 300ms after `onMapCreated` before fetching
- Use fallback default bounds if `getVisibleRegion()` fails
- Check `_isMapReady` flag before API calls

### Issue: Null pointer exceptions
**Solution**: 
- Always check `mounted` before `setState()`
- Validate all API response data before using
- Use null-safe operators (`?.`, `??`)

---

## ✅ Testing Checklist

### Basic Functionality
- [ ] Map loads without crashing
- [ ] Map controller initializes properly
- [ ] Initial billboards load successfully
- [ ] No null pointer exceptions

### Clustering
- [ ] Clustering works at low zoom levels
- [ ] Individual markers show at high zoom
- [ ] Cluster tap zooms in correctly
- [ ] Cluster count displays correctly

### Performance
- [ ] Debouncing prevents excessive API calls
- [ ] Bounds change detection works (5% threshold)
- [ ] Loading indicators appear during fetch
- [ ] Markers update when map bounds change

### Error Handling
- [ ] Error handling works for network failures
- [ ] App doesn't crash on API errors
- [ ] Timeout errors are handled gracefully
- [ ] Invalid data doesn't cause crashes

### User Experience
- [ ] Individual marker tap shows details
- [ ] Map panning is smooth
- [ ] No lag when zooming
- [ ] Error messages are user-friendly

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

---

## 🛡️ Crash Prevention Features

This guide includes **crash-safe** implementations with the following protections:

1. **Null Safety**: All bounds parameters are checked before use
2. **Mounted Checks**: Widget mounted state verified before setState
3. **Error Handling**: Try-catch blocks around all async operations
4. **Map Ready Check**: Waits for map initialization before fetching
5. **Data Validation**: Validates API response data before processing
6. **Timeout Protection**: API calls have 30-second timeout
7. **Bounds Change Detection**: Only fetches when bounds change significantly (5% threshold)
8. **Fallback Values**: Uses default bounds if getVisibleRegion() fails

### Key Crash Fixes Applied:

✅ **Map Controller Initialization**: 300ms delay after `onMapCreated`  
✅ **Null Bounds Check**: Returns early if bounds are null  
✅ **Mounted State Check**: Prevents setState on disposed widgets  
✅ **Data Validation**: Validates all API response fields  
✅ **Error Boundaries**: Try-catch around all critical operations  
✅ **Timeout Handling**: Prevents hanging requests  

These fixes ensure your app won't crash even if:
- Map isn't ready yet
- Network request fails
- API returns invalid data
- User navigates away during fetch
- Map controller is disposed

