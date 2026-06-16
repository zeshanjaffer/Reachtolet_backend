import django_filters
from django_filters import rest_framework as filters

from .geo_utils import apply_map_bounds_filter, apply_radius_filter
from .models import Billboard


class BillboardFilter(filters.FilterSet):
    """Billboard list filters: media type, city, tier, and PostGIS location."""

    ooh_media_type = filters.CharFilter(
        lookup_expr='iexact',
        help_text='Filter by media type (Digital Billboard, Static Billboard, etc.)',
    )
    city = filters.CharFilter(
        lookup_expr='icontains',
        help_text='Partial match on city name',
    )
    type = filters.CharFilter(
        field_name='type',
        lookup_expr='iexact',
        help_text='Board tier: Premium, Standard, etc.',
    )

    class Meta:
        model = Billboard
        fields = ['ooh_media_type', 'city', 'type']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        ne_lat = self.data.get('ne_lat')
        ne_lng = self.data.get('ne_lng')
        sw_lat = self.data.get('sw_lat')
        sw_lng = self.data.get('sw_lng')

        if ne_lat and ne_lng and sw_lat and sw_lng:
            return apply_map_bounds_filter(queryset, ne_lat, ne_lng, sw_lat, sw_lng)

        lat = self.data.get('lat')
        lng = self.data.get('lng')
        radius = self.data.get('radius')

        if lat and lng and radius:
            return apply_radius_filter(queryset, lat, lng, radius)

        return queryset
