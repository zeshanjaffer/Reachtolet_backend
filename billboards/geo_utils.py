"""PostGIS helpers for billboard map search and radius filters."""

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D


def point_from_lat_lng(lat, lng, srid=4326):
    """Build a WGS84 point (x=longitude, y=latitude)."""
    return Point(float(lng), float(lat), srid=srid)


def sync_billboard_location(billboard):
    """Set `location` from latitude/longitude when both are present."""
    if billboard.latitude is not None and billboard.longitude is not None:
        billboard.location = point_from_lat_lng(billboard.latitude, billboard.longitude)
    else:
        billboard.location = None


def apply_map_bounds_filter(queryset, ne_lat, ne_lng, sw_lat, sw_lng):
    """Filter billboards inside map viewport (PostGIS). Normalizes inverted drag bounds."""
    ne_lat, ne_lng = float(ne_lat), float(ne_lng)
    sw_lat, sw_lng = float(sw_lat), float(sw_lng)

    if ne_lat < sw_lat:
        ne_lat, sw_lat = sw_lat, ne_lat
    if ne_lng < sw_lng:
        ne_lng, sw_lng = sw_lng, ne_lng

    bbox = Polygon.from_bbox((sw_lng, sw_lat, ne_lng, ne_lat))

    return queryset.filter(
        location__isnull=False,
        location__within=bbox,
    )


def apply_radius_filter(queryset, lat, lng, radius_km):
    """
    True great-circle radius filter (PostGIS geography + ST_DWithin).
    Orders results nearest-first; annotates distance in meters as `distance_m`.
    """
    lat, lng, radius_km = float(lat), float(lng), float(radius_km)
    origin = point_from_lat_lng(lat, lng)

    return (
        queryset.filter(
            location__isnull=False,
            location__dwithin=(origin, D(km=radius_km)),
        )
        .annotate(distance_m=Distance('location', origin))
        .order_by('distance_m')
    )


def backfill_billboard_locations(Billboard):
    """Migration helper: populate location from existing lat/lng rows."""
    qs = Billboard.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    batch = []
    for billboard in qs.iterator(chunk_size=500):
        sync_billboard_location(billboard)
        batch.append(billboard)
        if len(batch) >= 500:
            Billboard.objects.bulk_update(batch, ['location'])
            batch.clear()
    if batch:
        Billboard.objects.bulk_update(batch, ['location'])
