"""Geospatial endpoints (spec Phase 2.2).

GET  /api/v1/geospatial/districts/            GeoJSON FeatureCollection (simplified)
POST /api/v1/geospatial/point-in-polygon/     reverse geocode {lat,lng} -> district/village
GET  /api/v1/geospatial/nearby/               districts within ?km= of ?lat=&lng=
"""
import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.claims.models import FRAClaim
from apps.geo import services
from apps.geo.models import District


def _feature(district, simplify_tolerance=0.01):
    geom = district.geometry
    if geom is not None and simplify_tolerance:
        geom = geom.simplify(simplify_tolerance, preserve_topology=True)
    return {
        "type": "Feature",
        "geometry": json.loads(geom.geojson) if geom is not None else None,
        "properties": {
            "district_code": district.district_code,
            "name": district.name_english,
            "state": district.state,
            "risk_score": float(district.risk_score) if district.risk_score is not None else None,
            "risk_category": district.risk_category,
            "tribal_population": district.tribal_population,
        },
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def districts_geojson(request):
    """GeoJSON FeatureCollection of districts (Douglas-Peucker simplified).

    Scoped to the caller's jurisdiction. Optional ?state= filter.
    """
    qs = District.objects.exclude(geometry__isnull=True)
    user = request.user
    if user.assigned_districts:
        qs = qs.filter(district_code__in=user.assigned_districts)
    elif user.assigned_states:
        qs = qs.filter(state__in=user.assigned_states)
    state = request.query_params.get("state")
    if state:
        qs = qs.filter(state=state)
    tol = float(request.query_params.get("simplify", 0.01))
    features = [_feature(d, tol) for d in qs[:1000]]
    return Response({"type": "FeatureCollection", "features": features,
                     "count": len(features)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def point_in_polygon(request):
    """Reverse geocode a coordinate to its containing district/village, with a
    count of FRA claims in that district."""
    try:
        lat = float(request.data["latitude"])
        lng = float(request.data["longitude"])
    except (KeyError, TypeError, ValueError):
        return Response({"detail": "latitude and longitude are required numbers"},
                        status=400)
    point = services.make_point(lat, lng)
    district = services.district_containing(point)
    village = services.village_containing(point)
    result = {
        "query": {"latitude": lat, "longitude": lng},
        "district": None, "village": None, "fra_claims_in_district": 0,
    }
    if district:
        result["district"] = {"district_code": district.district_code,
                              "name": district.name_english, "state": district.state}
        result["fra_claims_in_district"] = FRAClaim.objects.filter(district=district).count()
    if village:
        result["village"] = {"village_code": village.village_code,
                             "name": village.village_name}
    if not district:
        # graceful fallback: nearest districts so the client still gets context
        near = services.nearest_districts(point, limit=3)
        result["nearest_districts"] = [
            {"district_code": d.district_code, "name": d.name_english,
             "distance_km": round(d.distance.km, 1)} for d in near
        ]
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nearby_districts(request):
    try:
        lat = float(request.query_params["lat"])
        lng = float(request.query_params["lng"])
        km = float(request.query_params.get("km", 200))
    except (KeyError, ValueError):
        return Response({"detail": "lat, lng required; km optional"}, status=400)
    point = services.make_point(lat, lng)
    rows = services.districts_within_km(point, km)[:50]
    return Response({
        "center": {"latitude": lat, "longitude": lng}, "radius_km": km,
        "count": rows.count(),
        "districts": [{
            "district_code": d.district_code, "name": d.name_english, "state": d.state,
            "risk_category": d.risk_category,
            "distance_km": round(d.distance.km, 1),
        } for d in rows],
    })
