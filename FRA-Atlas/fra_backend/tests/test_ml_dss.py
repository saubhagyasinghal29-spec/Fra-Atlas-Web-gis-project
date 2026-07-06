import datetime
from decimal import Decimal

import pytest

from apps.common.enums import ClaimStatus

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------- inference -------
def test_onnx_prediction(risk_model, snapshot_factors):
    from apps.analytics.inference import get_active_predictor
    pred = get_active_predictor().predict(snapshot_factors)
    assert 0 <= pred["risk_score"] <= 100
    assert pred["risk_category"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert 0 <= pred["confidence"] <= 1
    assert pred["model_version"] == "test-1.0"


def test_missing_feature_raises(risk_model, snapshot_factors):
    from apps.analytics.inference import get_active_predictor
    broken = dict(snapshot_factors); broken.pop("Approval Rate")
    with pytest.raises(ValueError):
        get_active_predictor().predict(broken)


def test_shap_explanation(risk_model, snapshot_factors):
    from apps.analytics.inference import get_active_predictor
    exp = get_active_predictor().explain_prediction(snapshot_factors, top_k=3)
    assert len(exp["top_factors"]) == 3
    assert {"feature", "value", "shap"} <= set(exp["top_factors"][0])
    # contributions are sorted by |shap| descending
    mags = [abs(f["shap"]) for f in exp["top_factors"]]
    assert mags == sorted(mags, reverse=True)


def test_no_active_model_raises(db, snapshot_factors):
    from apps.analytics.inference import ModelNotAvailable, clear_predictor_cache, get_active_predictor
    clear_predictor_cache()
    with pytest.raises(ModelNotAvailable):
        get_active_predictor()


def test_predict_endpoint(admin_api, risk_model, district_with_snapshot):
    resp = admin_api.post("/api/v1/analytics/predict-district-risk/",
                          {"district_code": district_with_snapshot.district_code},
                          format="json")
    assert resp.status_code == 200
    assert "explanation" in resp.data and "risk_score" in resp.data


# ------------------------------------------------------------------ DSS ------
def _review_claim(field_officer, district_admin, district, community):
    from apps.claims import services
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("10"), claim_date=datetime.date(2024, 1, 1),
    )
    services.transition_claim(claim=claim, to_status=ClaimStatus.SUBMITTED,
                              actor=field_officer, reason="s")
    services.transition_claim(claim=claim, to_status=ClaimStatus.UNDER_REVIEW,
                              actor=district_admin, reason="r")
    return claim


def test_dss_high_risk_recommends_forest(field_officer, district_admin,
                                         district_with_snapshot, community):
    from apps.analytics.dss import generate_and_store
    claim = _review_claim(field_officer, district_admin, district_with_snapshot, community)
    recs = generate_and_store(claim)
    types = {r.recommendation_type for r in recs}
    assert "FOREST_MANAGEMENT" in types        # snapshot is high-risk
    assert "PROCESS_ACCELERATION" in types      # low approval / high pending
    assert all(0 <= float(r.confidence_score) <= 1 for r in recs)


def test_dss_is_idempotent(field_officer, district_admin, district_with_snapshot, community):
    from apps.analytics.dss import generate_and_store
    from apps.claims.models import DSSRecommendation
    claim = _review_claim(field_officer, district_admin, district_with_snapshot, community)
    generate_and_store(claim)
    first = DSSRecommendation.objects.filter(fra_claim=claim).count()
    generate_and_store(claim)  # within 7 days -> no duplicates
    assert DSSRecommendation.objects.filter(fra_claim=claim).count() == first


# ---------------------------------------------------------- celery tasks -----
def test_nightly_risk_task_writes_snapshots(risk_model, district_with_snapshot):
    from apps.analytics.models import DistrictRiskSnapshot
    from apps.analytics.tasks import compute_district_risk_scores
    before = DistrictRiskSnapshot.objects.count()
    result = compute_district_risk_scores.apply().get()
    assert result["status"] == "ok" and result["districts_scored"] >= 1
    assert DistrictRiskSnapshot.objects.count() > before
    district_with_snapshot.refresh_from_db()
    assert district_with_snapshot.risk_score is not None


def test_dss_task(field_officer, district_admin, district_with_snapshot, community):
    from apps.analytics.tasks import generate_dss_recommendations
    _review_claim(field_officer, district_admin, district_with_snapshot, community)
    result = generate_dss_recommendations.apply().get()
    assert result["status"] == "ok" and result["recommendations_created"] >= 1


def test_audit_verification_task(field_officer):
    from apps.audit.models import record_audit
    from apps.audit.tasks import verify_audit_log_integrity
    from apps.common.enums import AuditAction
    record_audit(entity_type="X", entity_id=field_officer.id, action=AuditAction.CREATE,
                 actor=field_officer, reason="r", new_state={})
    result = verify_audit_log_integrity.apply().get()
    assert result["status"] == "ok" and result["rows_total"] == 1
