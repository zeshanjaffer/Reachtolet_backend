# 🎯 Simple Billboard Filter API Guide

## 📋 **API Endpoint**
```
GET http://localhost:8000/api/billboards/
```

## 🔍 **Available Filters**

### **1. Media Type Filter**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ooh_media_type` | string | Filter by media type (exact match) | `?ooh_media_type=Digital Billboard` |

**Available Media Types:**
- `Digital Billboard`
- `Static Billboard`
- `LED Display`
- `Transit Media`

### **2. Location Filter (Radius Search)**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `lat` | number | Center latitude | `?lat=31.4591` |
| `lng` | number | Center longitude | `?lng=74.2429` |
| `radius` | number | Radius in kilometers | `?radius=10` |

### **3. Combined Filters**
You can combine both filters:
```
GET /api/billboards/?ooh_media_type=Digital Billboard&lat=31.4591&lng=74.2429&radius=10
```

---

## 🚀 **Frontend Implementation**

### **React Native Hook**
```javascript
const useBillboardFilter = () => {
  const [filters, setFilters] = useState({});
  const [billboards, setBillboards] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchBillboards = async (filterParams = {}) => {
    setLoading(true);
    try {
      const queryString = new URLSearchParams(filterParams).toString();
      const response = await fetch(`http://localhost:8000/api/billboards/?${queryString}`);
      const data = await response.json();
      setBillboards(data.results);
    } catch (error) {
      console.error('Error fetching billboards:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = (newFilters) => {
    setFilters(newFilters);
    fetchBillboards(newFilters);
  };

  return { billboards, loading, applyFilters, filters };
};
```

### **Filter Component**
```javascript
const BillboardFilter = () => {
  const { applyFilters, filters } = useBillboardFilter();

  const handleMediaTypeChange = (mediaType) => {
    applyFilters({ ...filters, ooh_media_type: mediaType });
  };

  const handleLocationFilter = async (radius = 10) => {
    try {
      // Get current location
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        alert('Permission to access location was denied');
        return;
      }

      const location = await Location.getCurrentPositionAsync({});
      const { latitude, longitude } = location.coords;

      // Apply location filter
      applyFilters({
        ...filters,
        lat: latitude,
        lng: longitude,
        radius: radius
      });
    } catch (error) {
      console.error('Error getting location:', error);
    }
  };

  return (
    <View>
      {/* Media Type Filter */}
      <Picker
        selectedValue={filters.ooh_media_type}
        onValueChange={handleMediaTypeChange}
      >
        <Picker.Item label="All Types" value="" />
        <Picker.Item label="Digital Billboard" value="Digital Billboard" />
        <Picker.Item label="Static Billboard" value="Static Billboard" />
        <Picker.Item label="LED Display" value="LED Display" />
        <Picker.Item label="Transit Media" value="Transit Media" />
      </Picker>

      {/* Location Filter */}
      <TouchableOpacity onPress={() => handleLocationFilter(10)}>
        <Text>Filter by Location (10km radius)</Text>
      </TouchableOpacity>

      {/* Clear Filters */}
      <TouchableOpacity onPress={() => applyFilters({})}>
        <Text>Clear All Filters</Text>
      </TouchableOpacity>
    </View>
  );
};
```

---

## 📱 **For Cursor AI**

**Tell Cursor AI to implement:**

1. **Filter Hook**: `useBillboardFilter` with state management
2. **Media Type Picker**: Dropdown for media type selection
3. **Location Filter**: Button to get user location and filter nearby billboards
4. **Clear Filters**: Button to reset all filters
5. **Loading States**: Show loading while fetching filtered results

**Key API Call:**
```javascript
const fetchBillboards = async (filters) => {
  const queryString = new URLSearchParams(filters).toString();
  const response = await fetch(`http://localhost:8000/api/billboards/?${queryString}`);
  return response.json();
};
```

**Filter Examples:**
- Media Type: `?ooh_media_type=Digital Billboard`
- Location: `?lat=31.4591&lng=74.2429&radius=10`
- Combined: `?ooh_media_type=Digital Billboard&lat=31.4591&lng=74.2429&radius=10`
