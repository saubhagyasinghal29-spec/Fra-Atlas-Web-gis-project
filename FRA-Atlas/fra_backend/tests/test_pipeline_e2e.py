"""End-to-end coverage of the data pipeline, analytics surface, and ops/ML
management commands against the real loaders."""
import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_geometry_generation():
    from apps.geo.geometry import district_centroid, generate_district_geometry
    geom, centroid = generate_district_geometry("Chhattisgarh", "CHH-001")
    assert geom.geom_type == "MultiPolygon"
    assert geom.contains(centroid)
    # deterministic
    assert district_centroid("Chhattisgarh", "CHH-001").coords == \
        district_centroid("Chhattisgarh", "CHH-001").coords


def test_full_pipeline_and_analytics(admin_api):
    """Load real data + train the model, then exercise the analytics surface,
    the scheduled tasks, and the governance commands end to end."""
    call_command("load_fra_data")
    call_command("train_risk_model")

    # analytics read endpoints
    assert admin_api.get("/api/v1/analytics/risk-model/status/").status_code == 200
    assert admin_api.get("/api/v1/analytics/factor-correlation/").status_code == 200
    assert admin_api.get("/api/v1/analytics/pca-clustering/").data["count"] > 0

    from apps.geo.models import District
    code = District.objects.exclude(risk_score__isnull=True).first().district_code
    assert admin_api.get(f"/api/v1/districts/{code}/risk/").status_code == 200
    summ = admin_api.get(f"/api/v1/districts/{code}/claims/summary/")
    assert summ.status_code == 200 and "source" in summ.data

    # live ONNX prediction + SHAP
    pred = admin_api.post("/api/v1/analytics/predict-district-risk/",
                          {"district_code": code}, format="json")
    assert pred.status_code == 200 and "explanation" in pred.data

    # scheduled analytics tasks
    from apps.analytics.tasks import (
        compute_correlation_factors, compute_district_risk_scores,
        monitor_prediction_drift, refresh_materialized_views,
    )
    assert compute_district_risk_scores.apply().get()["status"] == "ok"
    assert compute_correlation_factors.apply().get()["status"] == "ok"
    assert monitor_prediction_drift.apply().get()["status"] in {"ok", "DRIFT_DETECTED"}
    assert "refreshed" in refresh_materialized_views.apply().get()

    # governance + ops commands
    call_command("fairness_report")
    call_command("refresh_matviews")
    call_command("backup")
    from apps.ops.models import DataSnapshot
    snap = DataSnapshot.objects.latest("created_at")
    assert snap.verified
    call_command("restore", str(snap.id))


def test_analytics_endpoints_404_paths(admin_api):
    assert admin_api.get("/api/v1/analytics/risk-model/status/").status_code == 404
    assert admin_api.get("/api/v1/analytics/factor-correlation/").status_code == 404
    assert admin_api.get("/api/v1/districts/NOPE/risk/").status_code == 404
    assert admin_api.get("/api/v1/districts/NOPE/claims/summary/").status_code == 404


def test_report_download_and_status(admin_api):
    gen = admin_api.post("/api/v1/reports/generate/",
                         {"report_type": "district_claims", "export_format": "CSV"},
                         format="json")
    job_id = gen.data["job_id"]
    st = admin_api.get(f"/api/v1/reports/{job_id}/status/")
    assert st.status_code == 200 and st.data["status"] == "COMPLETE"
    dl = admin_api.get(f"/api/v1/reports/{job_id}/download/")
    assert dl.status_code == 200


def test_storage_signed_url_and_read():
    from apps.documents.services import get_storage
    s = get_storage()
    s.save("t/k.txt", b"hello")
    assert s.read("t/k.txt") == b"hello"
    assert s.signed_url("t/k.txt")
