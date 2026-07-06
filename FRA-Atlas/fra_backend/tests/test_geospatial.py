import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon

from apps.geo import services
from apps.geo.models import District

pytestmark = pytest.mark.django_db


def _box(cx, cy, half=0.2):
    ring = ((cx - half, cy - half), (cx - half, cy + half),
            (cx + half, cy + half), (cx + half, cy - half), (cx - half, cy - half))
    return MultiPolygon(Polygon(ring, srid=4326), srid=4326)


@pytest.fixture
def geo_districts(db):
    a = District.objects.create(
        district_code="GA-001", name_english="Alpha", state="StateA",
        geometry=_box(81.9, 21.3), centroid=Point(81.9, 21.3, srid=4326),
        risk_score=70, risk_category="CRITICAL",
    )
    b = District.objects.create(
        district_code="GB-001", name_english="Beta", state="StateB",
        geometry=_box(78.3, 23.5), centroid=Point(78.3, 23.5, srid=4326),
        risk_score=40, risk_category="LOW",
    )
    return a, b


def test_point_in_polygon_service(geo_districts):
    a, b = geo_districts
    assert services.district_containing(services.make_point(21.3, 81.9)).id == a.id
    assert services.district_containing(services.make_point(23.5, 78.3)).id == b.id
    # a point far away is contained by neither
    assert services.district_containing(services.make_point(10.0, 60.0)) is None


def test_nearest_and_within(geo_districts):
    a, b = geo_districts
    pt = services.make_point(21.3, 81.9)
    nearest = list(services.nearest_districts(pt, limit=2))
    assert nearest[0].id == a.id  # alpha is exactly at the point
    within = services.districts_within_km(pt, 50)
    assert a in within and b not in within  # beta is ~450km away


def test_point_in_polygon_endpoint(admin_api, geo_districts):
    resp = admin_api.post("/api/v1/geospatial/point-in-polygon/",
                          {"latitude": 21.3, "longitude": 81.9}, format="json")
    assert resp.status_code == 200
    assert resp.data["district"]["district_code"] == "GA-001"


def test_point_in_polygon_endpoint_miss_returns_nearest(admin_api, geo_districts):
    resp = admin_api.post("/api/v1/geospatial/point-in-polygon/",
                          {"latitude": 10.0, "longitude": 60.0}, format="json")
    assert resp.status_code == 200
    assert resp.data["district"] is None
    assert len(resp.data["nearest_districts"]) >= 1


def test_districts_geojson_endpoint(admin_api, geo_districts):
    # admin is scoped to TS-001 only by default; widen scope for this read
    admin_api.user.assigned_districts = ["GA-001", "GB-001"]
    admin_api.user.assigned_states = ["StateA", "StateB"]
    admin_api.user.save()
    resp = admin_api.get("/api/v1/geospatial/districts/")
    assert resp.status_code == 200
    assert resp.data["type"] == "FeatureCollection"
    assert resp.data["count"] == 2
    feat = resp.data["features"][0]
    assert feat["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert "risk_category" in feat["properties"]


def test_nearby_endpoint(admin_api, geo_districts):
    resp = admin_api.get("/api/v1/geospatial/nearby/?lat=21.3&lng=81.9&km=50")
    assert resp.status_code == 200
    codes = {d["district_code"] for d in resp.data["districts"]}
    assert "GA-001" in codes and "GB-001" not in codes
