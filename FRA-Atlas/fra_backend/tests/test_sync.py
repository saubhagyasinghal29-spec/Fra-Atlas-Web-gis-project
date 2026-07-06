import datetime
import json
import tempfile
from decimal import Decimal

import pytest

from apps.sync.client import SyncEngine

pytestmark = pytest.mark.django_db


def _bridge(api_client):
    """Adapt the SyncEngine HTTP interface onto the DRF test client."""
    def http(method, path, body=None):
        if method == "GET":
            resp = api_client.get(path)
        else:
            resp = api_client.post(path, body, format="json")
        assert resp.status_code == 200, (path, resp.status_code, resp.data)
        return resp.data
    return http


# ------------------------------------------------------------ server ---------
def test_pull_delta_and_checksum(admin_api, district):
    resp = admin_api.get("/api/v1/sync/pull/?entity=district")
    assert resp.status_code == 200
    assert resp.data["count"] >= 1
    assert resp.data["entity"] == "district"
    assert "checksum" in resp.data and "server_time" in resp.data


def test_pull_since_returns_only_newer(admin_api, district):
    first = admin_api.get("/api/v1/sync/pull/?entity=district")
    watermark = first.data["server_time"]
    # nothing changed after the watermark
    second = admin_api.get(f"/api/v1/sync/pull/?entity=district&since={watermark}")
    assert second.data["count"] == 0


def test_push_accepts_and_conflicts(admin_api, district, community):
    body = {"device_id": "dev-1", "claims": [
        {"client_ref": "c1", "district_code": district.district_code,
         "tribal_community_id": str(community.id), "claim_type": "CFR",
         "area_hectares": "12.5", "claim_date": "2024-03-01"},
        {"client_ref": "c2", "district_code": "DOES-NOT-EXIST",
         "tribal_community_id": str(community.id), "claim_type": "CFR",
         "area_hectares": "1", "claim_date": "2024-03-01"},
    ]}
    resp = admin_api.post("/api/v1/sync/push/", body, format="json")
    assert resp.status_code == 200
    assert resp.data["accepted_count"] == 1
    assert resp.data["conflict_count"] == 1
    from apps.claims.models import FRAClaim
    assert FRAClaim.objects.filter(district=district).count() == 1


# ------------------------------------------------------------ client ---------
def test_client_engine_pull_then_push(admin_api, district, community):
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        engine = SyncEngine(tmp.name, "http://test", "tok", http=_bridge(admin_api))
        engine.init_schema()

        pulled = engine.pull("district")
        assert pulled >= 1
        mirror = engine.db.execute("SELECT COUNT(*) c FROM mirror WHERE entity='district'").fetchone()
        assert mirror["c"] == pulled

        # offline create, then push
        engine.queue_claim("local-1", {
            "district_code": district.district_code,
            "tribal_community_id": str(community.id),
            "claim_type": "CFR", "area_hectares": "8", "claim_date": "2024-05-01"})
        result = engine.push(device_id="dev-1")
        assert result["accepted_count"] == 1
        row = engine.db.execute(
            "SELECT sync_status, server_id FROM pending_claims WHERE client_ref='local-1'"
        ).fetchone()
        assert row["sync_status"] == "SYNCED" and row["server_id"]


def test_client_detects_checksum_corruption(admin_api, district):
    def corrupt_http(method, path, body=None):
        data = _bridge(admin_api)(method, path, body)
        if "pull" in path:
            data = dict(data); data["checksum"] = "tampered"
        return data
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        engine = SyncEngine(tmp.name, "http://test", "tok", http=corrupt_http)
        engine.init_schema()
        with pytest.raises(ValueError):
            engine.pull("district")
