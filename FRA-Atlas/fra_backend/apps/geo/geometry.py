"""Geometry generation for districts that lack boundary data.

The shipped dataset has no coordinates, so we place each district near its
state's *real* approximate centroid (lat/lon below) with a deterministic,
seed-stable jitter, then build a small square polygon around it. This makes
spatial queries meaningful (a point in Chhattisgarh resolves to a Chhattisgarh
district) while being explicit that district-level boundaries are synthetic
placeholders.

Production: replace generate_district_geometry() with an ingest of real
boundaries (e.g. Census/data.gov.in district shapefiles -> GEOSGeometry). No
query code changes -- only the geometry source does.
"""
import hashlib

from django.contrib.gis.geos import MultiPolygon, Point, Polygon

# Approximate state centroids (lat, lon), decimal degrees. Real values.
STATE_CENTROIDS = {
    "Arunachal Pradesh": (28.10, 94.20),
    "Assam": (26.20, 92.90),
    "Chhattisgarh": (21.30, 81.90),
    "Gujarat": (22.70, 71.50),
    "Himachal Pradesh": (31.80, 77.30),
    "Jharkhand": (23.60, 85.30),
    "Kerala": (10.40, 76.30),
    "Madhya Pradesh": (23.50, 78.30),
    "Maharashtra": (19.40, 76.10),
    "Meghalaya": (25.50, 91.30),
    "Nagaland": (26.10, 94.50),
    "Odisha": (20.50, 84.50),
    "Rajasthan": (26.60, 73.80),
    "Telangana": (17.90, 79.00),
    "Tripura": (23.80, 91.50),
    "Uttarakhand": (30.10, 79.20),
}

DEFAULT_CENTROID = (22.0, 79.0)  # central India fallback


def _jitter(seed_text: str, spread: float = 1.6):
    """Deterministic [-spread, spread] offsets from a hash of the seed text."""
    h = hashlib.sha256(seed_text.encode()).digest()
    fx = int.from_bytes(h[0:4], "big") / 0xFFFFFFFF  # 0..1
    fy = int.from_bytes(h[4:8], "big") / 0xFFFFFFFF
    return (fx - 0.5) * 2 * spread, (fy - 0.5) * 2 * spread


def district_centroid(state: str, district_code: str) -> Point:
    base_lat, base_lon = STATE_CENTROIDS.get(state, DEFAULT_CENTROID)
    dlat, dlon = _jitter(f"{state}:{district_code}")
    return Point(base_lon + dlon, base_lat + dlat, srid=4326)


def generate_district_geometry(state: str, district_code: str):
    """Return (MultiPolygon, centroid Point) for a district."""
    c = district_centroid(state, district_code)
    half = 0.18  # ~20km box
    lon, lat = c.x, c.y
    ring = (
        (lon - half, lat - half), (lon - half, lat + half),
        (lon + half, lat + half), (lon + half, lat - half),
        (lon - half, lat - half),
    )
    poly = Polygon(ring, srid=4326)
    return MultiPolygon(poly, srid=4326), c
