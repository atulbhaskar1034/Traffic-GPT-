"""
Geospatial utility functions for the GRIDLOCK pipeline.

Handles GPS validation, geofencing (point-in-polygon), and
distance calculations for the Bangalore city boundary.
"""

import json
from pathlib import Path
from typing import Optional, Tuple

from shapely.geometry import Point, shape

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Default geofence path ────────────────────────────────────
_GEOFENCE_PATH = Path("configs/geofence/bangalore_boundary.geojson")
_cached_boundary = None


def _load_boundary(geojson_path: Optional[Path] = None):
    """Load and cache the Bangalore city boundary polygon.

    Args:
        geojson_path: Path to the GeoJSON boundary file.

    Returns:
        Shapely Polygon of the city boundary.
    """
    global _cached_boundary
    if _cached_boundary is not None:
        return _cached_boundary

    path = geojson_path or _GEOFENCE_PATH
    with open(path, "r") as f:
        geojson = json.load(f)

    _cached_boundary = shape(geojson["geometry"])
    logger.info(f"Loaded Bangalore boundary from {path}")
    return _cached_boundary


def is_within_bangalore(
    latitude: float,
    longitude: float,
    geojson_path: Optional[Path] = None,
) -> bool:
    """Check if a GPS coordinate falls within the Bangalore city boundary.

    Args:
        latitude: GPS latitude (e.g., 12.9716).
        longitude: GPS longitude (e.g., 77.5946).
        geojson_path: Optional custom boundary file path.

    Returns:
        True if the point is inside Bangalore.
    """
    boundary = _load_boundary(geojson_path)
    point = Point(longitude, latitude)  # GeoJSON uses (lon, lat) order
    result = boundary.contains(point)
    logger.debug(f"GPS ({latitude}, {longitude}) in Bangalore: {result}")
    return result


def validate_gps(
    latitude: Optional[float],
    longitude: Optional[float],
) -> dict:
    """Validate GPS coordinates for basic sanity.

    Args:
        latitude: GPS latitude.
        longitude: GPS longitude.

    Returns:
        Dictionary with validation results.
    """
    result = {
        "gps_present": latitude is not None and longitude is not None,
        "gps_valid": False,
        "in_bangalore": False,
    }

    if not result["gps_present"]:
        return result

    # Basic range check
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return result

    result["gps_valid"] = True
    result["in_bangalore"] = is_within_bangalore(latitude, longitude)
    return result


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the great-circle distance between two GPS points.

    Args:
        lat1, lon1: First point coordinates.
        lat2, lon2: Second point coordinates.

    Returns:
        Distance in meters.
    """
    import math

    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
