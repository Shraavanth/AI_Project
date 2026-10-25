"""
Geographic helpers.

All positions in the project are real latitude / longitude pairs.
- Distances use the Haversine formula (great-circle distance on a sphere).
- Movement converts "move N metres toward the target" into a new lat/lng by
  interpolating along the straight line, which is accurate for the few-km
  areas used here.
"""

import math

EARTH_RADIUS_M = 6371000.0
METRES_PER_DEG_LAT = 111320.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def offset(lat: float, lng: float, north_m: float, east_m: float):
    """Return the point that is north_m metres north and east_m metres east of (lat, lng)."""
    new_lat = lat + north_m / METRES_PER_DEG_LAT
    lng_scale = max(abs(math.cos(math.radians(lat))), 0.01)
    new_lng = lng + east_m / (METRES_PER_DEG_LAT * lng_scale)
    new_lat = max(-89.9, min(89.9, new_lat))
    new_lng = (new_lng + 180.0) % 360.0 - 180.0
    return new_lat, new_lng


def move_towards(lat: float, lng: float, target_lat: float, target_lng: float, step_m: float):
    """
    Move at most step_m metres from (lat, lng) toward the target.
    Returns (new_lat, new_lng, distance_moved_m, arrived).
    """
    distance = haversine_m(lat, lng, target_lat, target_lng)
    if distance <= step_m or distance < 0.01:
        return target_lat, target_lng, distance, True
    fraction = step_m / distance
    new_lat = lat + (target_lat - lat) * fraction
    new_lng = lng + (target_lng - lng) * fraction
    return new_lat, new_lng, step_m, False


def ring_point(center_lat: float, center_lng: float, distance_m: float, angle_rad: float):
    """Point at a given distance and angle (0 = east, counter-clockwise) from a centre."""
    return offset(center_lat, center_lng,
                  north_m=distance_m * math.sin(angle_rad),
                  east_m=distance_m * math.cos(angle_rad))


def segment_distance_m(lat1: float, lng1: float, lat2: float, lng2: float, p_lat: float, p_lng: float) -> float:
    """
    Geographical distance (in metres) from a point P(p_lat, p_lng) to a line segment A(lat1, lng1) -> B(lat2, lng2).
    Uses local tangent projection centered on P, accurate across local geographic areas.
    """
    scale_y = METRES_PER_DEG_LAT
    scale_x = METRES_PER_DEG_LAT * max(abs(math.cos(math.radians(p_lat))), 0.01)

    ax = (lng1 - p_lng) * scale_x
    ay = (lat1 - p_lat) * scale_y
    bx = (lng2 - p_lng) * scale_x
    by = (lat2 - p_lat) * scale_y

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-6:
        return math.hypot(ax, ay)

    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / seg_len_sq))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return math.hypot(closest_x, closest_y)

