"""Read-only analytics endpoints fed by nightly-computed snapshots.

GET /api/v1/analytics/risk-model/status/
GET /api/v1/analytics/factor-correlation/
GET /api/v1/analytics/pca-clustering/
GET /api/v1/districts/<code>/risk/
GET /api/v1/districts/<code>/claims/summary/
"""
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import (
    DistrictRiskSnapshot,
    FactorCorrelationMatrix,
    RiskPredictionModel,
)
from apps.claims.models import FRAClaim
from apps.common.enums import ClaimStatus
from apps.geo.models import District


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def risk_model_status(request):
    model = RiskPredictionModel.objects.filter(is_active=True).first()
    if not model:
        return Response({"detail": "No active model"}, status=404)
    return Response({
        "model_version": model.version,
        "deployed_at": model.deployed_at,
        "roc_auc": model.roc_auc,
        "pr_auc": model.pr_auc,
        "feature_importance": model.feature_importance_json,
        "feature_list": model.feature_list,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def factor_correlation(request):
    matrix = FactorCorrelationMatrix.objects.order_by("-created_at").first()
    if not matrix:
        return Response({"detail": "Not computed yet"}, status=404)
    return Response({
        "method": matrix.method,
        "factors": matrix.factors,
        "sample_size": matrix.sample_size,
        "matrix": matrix.matrix_json,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pca_clustering(request):
    """District-level PCA coordinates + cluster for the front-end scatter plot."""
    rows = (DistrictRiskSnapshot.objects.select_related("district")
            .order_by("district__district_code"))
    latest = {}
    for snap in rows:
        latest[snap.district_id] = snap  # ordered import => last wins == newest
    data = [{
        "district_code": s.district.district_code,
        "name": s.district.name_english,
        "state": s.district.state,
        "pc1": s.pc1, "pc2": s.pc2, "cluster": s.cluster,
        "risk_category": s.risk_category, "risk_score": s.risk_score,
    } for s in latest.values()]
    return Response({"count": len(data), "points": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def district_risk(request, district_code):
    district = District.objects.filter(district_code=district_code).first()
    if not district:
        return Response({"detail": "District not found"}, status=404)
    snap = (DistrictRiskSnapshot.objects.filter(district=district)
            .order_by("-prediction_timestamp").first())
    if not snap:
        return Response({"detail": "No risk snapshot"}, status=404)
    return Response({
        "district_code": district.district_code,
        "name": district.name_english,
        "state": district.state,
        "risk_score": snap.risk_score,
        "risk_category": snap.risk_category,
        "risk_rank": snap.risk_rank,
        "cluster": snap.cluster,
        "factors": snap.factors_json,
        "computed_at": snap.prediction_timestamp,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def district_claims_summary(request, district_code):
    district = District.objects.filter(district_code=district_code).first()
    if not district:
        return Response({"detail": "District not found"}, status=404)

    # Fast path: pre-computed materialized view (Postgres). Falls back to live
    # ORM aggregation on SpatiaLite/dev or before the first matview refresh.
    from apps.analytics.matviews import district_summary_row
    mv = district_summary_row(district_code)
    if mv:
        agg = mv
    else:
        agg = FRAClaim.objects.filter(district=district).aggregate(
            total_claims=Count("id"),
            approved_claims=Count("id", filter=Q(status=ClaimStatus.APPROVED)),
            pending_claims=Count("id", filter=Q(status=ClaimStatus.UNDER_REVIEW)),
            unique_communities=Count("tribal_community", distinct=True),
        )
    total = agg["total_claims"] or 0
    approval_rate = round(100.0 * (agg["approved_claims"] or 0) / total, 2) if total else 0.0
    return Response({
        "district_code": district.district_code,
        "total_claims": total,
        "approved_claims": agg["approved_claims"],
        "pending_claims": agg["pending_claims"],
        "approval_rate": approval_rate,
        "unique_communities": agg["unique_communities"],
        "risk_score": district.risk_score,
        "risk_category": district.risk_category,
        "source": "materialized_view" if mv else "live_query",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def predict_district_risk(request):
    """Live risk inference + SHAP explanation for a district.

    Body: {"district_code": "CHH-001"}  ->  ONNX prediction over the district's
    latest factor vector, with top SHAP contributions.
    """
    from apps.analytics.inference import ModelNotAvailable, get_active_predictor

    code = request.data.get("district_code")
    district = District.objects.filter(district_code=code).first()
    if not district:
        return Response({"detail": "District not found"}, status=404)
    snap = (DistrictRiskSnapshot.objects.filter(district=district)
            .order_by("-prediction_timestamp").first())
    if not snap or not snap.factors_json:
        return Response({"detail": "No feature vector for district"}, status=404)
    try:
        predictor = get_active_predictor()
        prediction = predictor.predict(snap.factors_json)
        explanation = predictor.explain_prediction(snap.factors_json)
    except ModelNotAvailable as exc:
        return Response({"detail": str(exc)}, status=503)
    return Response({
        "district_code": district.district_code,
        "name": district.name_english,
        **prediction,
        "explanation": explanation,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def districts_atlas(request):
    """All districts with live risk fields + governance factors, mapped to the
    portal's data model. Backs the dashboard, map, analytics, and DSS views."""
    from apps.analytics.models import DistrictRiskSnapshot

    # latest snapshot per district (factors, pca, cluster, rank)
    snaps = {}
    for s in DistrictRiskSnapshot.objects.select_related("district").order_by("prediction_timestamp"):
        snaps[s.district_id] = s

    cat_map = {"CRITICAL": "Critical", "MODERATE": "Moderate",
               "GOOD": "Good", "EXCELLENT": "Excellent"}
    rows = []
    for d in District.objects.all():
        s = snaps.get(d.id)
        f = (s.factors_json if s else {}) or {}
        rows.append({
            "state": d.state,
            "district": d.name_english,
            "code": d.district_code,
            "ri": float(d.risk_score) if d.risk_score is not None else None,
            "rl": cat_map.get(d.risk_category, d.risk_category),
            "rr": s.risk_rank if s else None,
            "cl": s.cluster if s else None,
            "pc1": s.pc1 if s else None,
            "pc2": s.pc2 if s else None,
            "ar": f.get("Approval Rate"),
            "pr": f.get("Pending Claims Rate"),
            "pt": f.get("Avg Processing Time"),
            "fl": f.get("Forest Loss Rate"),
            "tc": f.get("Tribal Pop. Coverage"),
            "cr": f.get("CFR Recognition Rate"),
            "rjr": f.get("Rejection Rate"),
            "enc": f.get("Encroachment Density"),
        })
    return Response({"count": len(rows), "districts": rows})
