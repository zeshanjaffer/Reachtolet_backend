import django_filters
from django_filters import rest_framework as filters
from .models import Billboard

class BillboardFilter(filters.FilterSet):
    """Simple filter for billboards - media type and location only"""
    
    # Media type filter
    ooh_media_type = filters.CharFilter(lookup_expr='iexact', help_text="Filter by media type (Digital Billboard, Static Billboard, etc.)")
    
    # Location-based filters
    lat = filters.NumberFilter(help_text="Center latitude for radius search")
    lng = filters.NumberFilter(help_text="Center longitude for radius search")
    radius = filters.NumberFilter(help_text="Radius in kilometers for location-based search")
    
    class Meta:
        model = Billboard
        fields = ['ooh_media_type']
    
    def filter_queryset(self, queryset):
        """Apply location-based filtering if coordinates provided"""
        queryset = super().filter_queryset(queryset)
        
        lat = self.data.get('lat')
        lng = self.data.get('lng')
        radius = self.data.get('radius')
        
        if lat and lng and radius:
            # Simple distance calculation (approximate)
            lat_min = lat - (radius / 111.0)  # 1 degree ≈ 111 km
            lat_max = lat + (radius / 111.0)
            lng_min = lng - (radius / (111.0 * abs(lat)))
            lng_max = lng + (radius / (111.0 * abs(lat)))
            
            queryset = queryset.filter(
                latitude__gte=lat_min,
                latitude__lte=lat_max,
                longitude__gte=lng_min,
                longitude__lte=lng_max
            )
        
        return queryset
