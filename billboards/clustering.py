"""
Grid-based clustering for billboards on maps.
Similar to Uber/Airbnb approach - groups nearby billboards into clusters.
"""
from collections import defaultdict
from typing import List, Dict, Any
import math


def calculate_grid_size(zoom_level: float) -> float:
    """
    Calculate grid cell size based on zoom level.
    Higher zoom = smaller grid cells = more detailed clusters.
    
    Args:
        zoom_level: Map zoom level (typically 1-20)
    
    Returns:
        Grid cell size in degrees
    """
    # Base grid size decreases as zoom increases
    # At zoom 1: ~10 degrees (country level)
    # At zoom 10: ~0.01 degrees (city level)
    # At zoom 15: ~0.001 degrees (street level)
    
    if zoom_level <= 5:
        return 1.0  # Large cells for country/region view
    elif zoom_level <= 10:
        return 0.1  # Medium cells for city view
    elif zoom_level <= 15:
        return 0.01  # Small cells for neighborhood view
    else:
        return 0.001  # Very small cells for street view


def get_grid_key(lat: float, lng: float, grid_size: float) -> tuple:
    """
    Get grid cell key for a coordinate.
    
    Args:
        lat: Latitude
        lng: Longitude
        grid_size: Size of grid cell in degrees
    
    Returns:
        Tuple of (grid_lat, grid_lng) representing the grid cell
    """
    grid_lat = math.floor(lat / grid_size) * grid_size
    grid_lng = math.floor(lng / grid_size) * grid_size
    return (grid_lat, grid_lng)


def create_cluster(billboards: List[Dict], grid_lat: float, grid_lng: float) -> Dict:
    """
    Create a cluster from a list of billboards in the same grid cell.
    
    Args:
        billboards: List of billboard dictionaries
        grid_lat: Grid cell latitude
        grid_lng: Grid cell longitude
    
    Returns:
        Cluster dictionary with center point, count, and bounds
    """
    if not billboards:
        return None
    
    # If only one billboard, return it as individual marker (not a cluster)
    if len(billboards) == 1:
        return {
            'type': 'marker',
            'id': billboards[0]['id'],
            'latitude': billboards[0]['latitude'],
            'longitude': billboards[0]['longitude'],
            'data': billboards[0]
        }
    
    # Calculate cluster center (average of all billboards in cluster)
    total_lat = sum(b['latitude'] for b in billboards)
    total_lng = sum(b['longitude'] for b in billboards)
    count = len(billboards)
    
    center_lat = total_lat / count
    center_lng = total_lng / count
    
    # Calculate bounds (min/max lat/lng of all billboards)
    lats = [b['latitude'] for b in billboards]
    lngs = [b['longitude'] for b in billboards]
    
    return {
        'type': 'cluster',
        'latitude': center_lat,
        'longitude': center_lng,
        'count': count,
        'bounds': {
            'ne_lat': max(lats),
            'ne_lng': max(lngs),
            'sw_lat': min(lats),
            'sw_lng': min(lngs)
        },
        'grid_lat': grid_lat,
        'grid_lng': grid_lng
    }


def cluster_billboards(billboards: List[Dict], zoom_level: float = 10.0) -> List[Dict]:
    """
    Cluster billboards into groups based on proximity and zoom level.
    
    Args:
        billboards: List of billboard dictionaries with 'latitude' and 'longitude'
        zoom_level: Map zoom level (1-20, default 10)
    
    Returns:
        List of clusters and individual markers
    """
    if not billboards:
        return []
    
    # Calculate grid size based on zoom level
    grid_size = calculate_grid_size(zoom_level)
    
    # Group billboards by grid cell
    grid_groups = defaultdict(list)
    
    for billboard in billboards:
        if billboard.get('latitude') is None or billboard.get('longitude') is None:
            continue  # Skip billboards without coordinates
        
        grid_key = get_grid_key(
            billboard['latitude'],
            billboard['longitude'],
            grid_size
        )
        grid_groups[grid_key].append(billboard)
    
    # Create clusters from grid groups
    clusters = []
    for (grid_lat, grid_lng), group_billboards in grid_groups.items():
        cluster = create_cluster(group_billboards, grid_lat, grid_lng)
        if cluster:
            clusters.append(cluster)
    
    return clusters


def should_use_clustering(zoom_level: float, billboard_count: int) -> bool:
    """
    Determine if clustering should be used based on zoom level and billboard count.
    
    Args:
        zoom_level: Map zoom level
        billboard_count: Number of billboards in the visible area
    
    Returns:
        True if clustering should be used, False otherwise
    """
    # Always cluster if zoom is low (zoomed out)
    if zoom_level < 12:
        return True
    
    # Cluster if there are many billboards even at higher zoom
    if billboard_count > 100:
        return True
    
    # Don't cluster if zoomed in close and few billboards
    return False

