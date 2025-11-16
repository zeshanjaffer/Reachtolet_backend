import django_filters
from django_filters import rest_framework as filters
from .models import Billboard

class BillboardFilter(filters.FilterSet):
    """Simple filter for billboards - media type and location only"""
    
    # Media type filter
    ooh_media_type = filters.CharFilter(lookup_expr='iexact', help_text="Filter by media type (Digital Billboard, Static Billboard, etc.)")
    
    # Location-based filters - Radius search
    lat = filters.NumberFilter(help_text="Center latitude for radius search")
    lng = filters.NumberFilter(help_text="Center longitude for radius search")
    radius = filters.NumberFilter(help_text="Radius in kilometers for location-based search")
    
    # Map bounds filters - For map viewport (preferred for map views)
    ne_lat = filters.NumberFilter(help_text="Northeast latitude (map bounds)")
    ne_lng = filters.NumberFilter(help_text="Northeast longitude (map bounds)")
    sw_lat = filters.NumberFilter(help_text="Southwest latitude (map bounds)")
    sw_lng = filters.NumberFilter(help_text="Southwest longitude (map bounds)")
    
    class Meta:
        model = Billboard
        fields = ['ooh_media_type']
    
    def filter_queryset(self, queryset):
        """Apply location-based filtering if coordinates provided"""
        queryset = super().filter_queryset(queryset)
        
        # Priority 1: Map bounds filtering (for map views)
        ne_lat = self.data.get('ne_lat')
        ne_lng = self.data.get('ne_lng')
        sw_lat = self.data.get('sw_lat')
        sw_lng = self.data.get('sw_lng')
        
        if ne_lat and ne_lng and sw_lat and sw_lng:
            # Map bounds filtering - most efficient for map views
            queryset = queryset.filter(
                latitude__gte=float(sw_lat),
                latitude__lte=float(ne_lat),
                longitude__gte=float(sw_lng),
                longitude__lte=float(ne_lng)
            )
        else:
            # Priority 2: Radius-based filtering (fallback)
            lat = self.data.get('lat')
            lng = self.data.get('lng')
            radius = self.data.get('radius')
            
            if lat and lng and radius:
                # Simple distance calculation (approximate)
                lat_min = float(lat) - (float(radius) / 111.0)  # 1 degree ≈ 111 km
                lat_max = float(lat) + (float(radius) / 111.0)
                lng_min = float(lng) - (float(radius) / (111.0 * abs(float(lat))))
                lng_max = float(lng) + (float(radius) / (111.0 * abs(float(lat))))
                
                queryset = queryset.filter(
                    latitude__gte=lat_min,
                    latitude__lte=lat_max,
                    longitude__gte=lng_min,
                    longitude__lte=lng_max
                )
        
        return queryset
