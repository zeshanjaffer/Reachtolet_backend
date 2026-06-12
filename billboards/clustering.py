"""
Production-grade map clustering for billboards using the Supercluster algorithm.

Algorithm: Supercluster (same as Mapbox, Airbnb, Google Maps)
  - Builds a multi-level KD-tree index once per dataset
  - At each zoom level, returns true spatial clusters (radius-based, not grid-based)
  - Clusters expand smoothly as the user zooms in
  - 10-100x faster than the old grid approach

The index is rebuilt whenever the billboard dataset changes (cache-version bump).
Between rebuilds it is held in process memory and served in microseconds.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supercluster parameters (tune for your data density and map tile size)
# ---------------------------------------------------------------------------
_SUPERCLUSTER_OPTIONS: dict[str, Any] = {
    "min_zoom": 0,
    "max_zoom": 16,
    "min_points": 2,     # minimum points required to form a cluster
    "radius": 60,        # pixel radius; increase → larger clusters
    "extent": 512,       # tile extent (standard Mapbox/Google value)
    "node_size": 64,     # KD-tree leaf node size (trade-off: speed vs memory)
}

# ---------------------------------------------------------------------------
# In-process index cache (per process/worker)
# ---------------------------------------------------------------------------
_INDEX_CACHE_VERSION_KEY = "billboard_cluster_index_version"
_INDEX_CACHE: dict[str, Any] = {
    "version": None,
    "index": None,
    "point_map": None,   # maps array-position → billboard_id
}


def _build_index(billboards: list[dict]) -> tuple[Any, list[int]]:
    """
    Build a SuperCluster index from a list of billboard dicts.

    Each dict must have 'id', 'latitude', 'longitude' keys.
    Points without valid coordinates are silently skipped.

    Returns (index, point_map) where point_map[i] = billboard_id for position i.
    """
    from python_supercluster import SuperCluster  # deferred import

    points: list[list[float]] = []
    point_map: list[int] = []

    for b in billboards:
        lat = b.get("latitude")
        lng = b.get("longitude")
        if lat is None or lng is None:
            continue
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat_f <= 90) or not (-180 <= lng_f <= 180):
            continue
        points.append([lng_f, lat_f])   # SuperCluster expects [lng, lat]
        point_map.append(b["id"])

    index = SuperCluster(_SUPERCLUSTER_OPTIONS)
    if points:
        index.load(points)

    logger.debug("Supercluster index built: %d points", len(points))
    return index, point_map


def _get_or_build_index(billboards: list[dict]) -> tuple[Any, list[int]]:
    """
    Return a cached SuperCluster index if the cache version matches,
    otherwise rebuild it.
    """
    from .signals import get_cache_version

    current_version = get_cache_version()

    if (
        _INDEX_CACHE["version"] == current_version
        and _INDEX_CACHE["index"] is not None
    ):
        return _INDEX_CACHE["index"], _INDEX_CACHE["point_map"]

    index, point_map = _build_index(billboards)
    _INDEX_CACHE["version"] = current_version
    _INDEX_CACHE["index"] = index
    _INDEX_CACHE["point_map"] = point_map
    return index, point_map


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cluster_billboards(
    billboards: list[dict],
    zoom_level: float = 10.0,
    bbox: dict | None = None,
) -> list[dict]:
    """
    Return clusters + individual markers for the given zoom and bounding box.

    Args:
        billboards: list of dicts with at minimum {id, latitude, longitude}
        zoom_level: float zoom level from the map client (0–20)
        bbox: optional dict {ne_lat, ne_lng, sw_lat, sw_lng}; if None, uses
              the full-world bounding box

    Response shape per item:

    Cluster:
        {
          "type": "cluster",
          "cluster_id": <int>,         # use with /api/billboards/cluster/{id}/leaves/
          "latitude": <float>,
          "longitude": <float>,
          "count": <int>,              # total points in this cluster
          "expansion_zoom": <int|null> # zoom level at which this cluster expands
        }

    Individual marker:
        {
          "type": "marker",
          "id": <int>,                 # billboard_id
          "latitude": <float>,
          "longitude": <float>,
          "count": 1
        }
    """
    if not billboards:
        return []

    zoom_int = max(0, min(16, int(math.floor(zoom_level))))

    if bbox:
        try:
            west  = float(bbox["sw_lng"])
            south = float(bbox["sw_lat"])
            east  = float(bbox["ne_lng"])
            north = float(bbox["ne_lat"])
        except (KeyError, TypeError, ValueError):
            west, south, east, north = -180, -90, 180, 90
    else:
        west, south, east, north = -180, -90, 180, 90

    sc_bbox = [west, south, east, north]  # [west_lng, south_lat, east_lng, north_lat]

    index, point_map = _get_or_build_index(billboards)

    if not point_map:
        return []

    try:
        raw = index.get_clusters(sc_bbox, zoom_int)
    except Exception as exc:  # noqa: BLE001
        logger.error("SuperCluster.get_clusters failed: %s", exc)
        return _fallback_markers(billboards)

    result: list[dict] = []
    for item in raw:
        count = item.get("count", 0)
        lat = item.get("lat")
        lng = item.get("lng")
        if lat is None or lng is None:
            continue

        if count and float(count) > 0:
            # --- cluster ---
            expansion = item.get("expansion_zoom")
            result.append({
                "type": "cluster",
                "cluster_id": int(item["id"]),
                "latitude": float(lat),
                "longitude": float(lng),
                "count": int(count),
                "expansion_zoom": int(expansion) if expansion is not None else None,
            })
        else:
            # --- individual marker ---
            point_index = int(item["id"])
            billboard_id = (
                point_map[point_index]
                if 0 <= point_index < len(point_map)
                else None
            )
            if billboard_id is None:
                continue
            result.append({
                "type": "marker",
                "id": billboard_id,
                "latitude": float(lat),
                "longitude": float(lng),
                "count": 1,
            })

    return result


def _fallback_markers(billboards: list[dict]) -> list[dict]:
    """Return individual markers for every billboard that has coordinates."""
    out = []
    for b in billboards:
        if b.get("latitude") is None or b.get("longitude") is None:
            continue
        out.append({
            "type": "marker",
            "id": b["id"],
            "latitude": float(b["latitude"]),
            "longitude": float(b["longitude"]),
            "count": 1,
        })
    return out


def should_use_clustering(zoom_level: float, billboard_count: int) -> bool:
    """
    Return True when clustering should be applied.

    Always cluster below zoom 12; cluster at higher zooms only when
    there are many billboards visible (avoids unnecessary work on
    zoomed-in views with few markers).
    """
    if zoom_level < 12:
        return True
    return billboard_count > 50


def invalidate_cluster_index() -> None:
    """Force rebuild of the in-process Supercluster index on next request."""
    _INDEX_CACHE["version"] = None
    _INDEX_CACHE["index"] = None
    _INDEX_CACHE["point_map"] = None
