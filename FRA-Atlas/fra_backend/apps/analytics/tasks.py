"""Scheduled analytics jobs.

Each task is idempotent and returns a small JSON summary (record counts +
duration) suitable for a BatchJob log / monitoring. They can be run by a worker
on the beat schedule, or synchronously in tests via `.apply()`.
"""
import statistics
import time

from celery import shared_task
from django.utils import timezone

from apps.analytics.dss import generate_and_store
from apps.analytics.inference import ModelNotAvailable, get_active_predictor
from apps.analytics.models import (
    DistrictRiskSnapshot,
    FactorCorrelationMatrix,
)
from apps.claims.models import FRAClaim
from apps.common.enums import ClaimStatus
from apps.geo.models import District


@shared_task(bind=True, max_retries=3)
def compute_district_risk_scores(self):
    """Re-score every district with the active model, write a fresh snapshot,
    and refresh the denormalized risk on the District row."""
    started = time.monotonic()
    try:
        predictor = get_active_predictor()
    except ModelNotAvailable as exc:
        return {"status": "skipped", "reason": str(exc)}

    now = timezone.now()
    updated = 0
    for district in District.objects.all():
        last = (DistrictRiskSnapshot.objects.filter(district=district)
                .order_by("-prediction_timestamp").first())
        if not last or not last.factors_json:
            continue
        result = predictor.predict(last.factors_json)
        try:
            explanation = predictor.explain_prediction(last.factors_json)
        except ModelNotAvailable:
            explanation = {}
        DistrictRiskSnapshot.objects.create(
            district=district, model_version=result["model_version"],
            risk_score=result["risk_score"], risk_category=result["risk_category"],
            risk_rank=last.risk_rank, cluster=last.cluster,
            pc1=last.pc1, pc2=last.pc2, factors_json=last.factors_json,
            shap_explanation_json=explanation, prediction_timestamp=now,
        )
        district.risk_score = result["risk_score"]
        district.risk_category = result["risk_category"]
        district.last_risk_update_at = now
        district.save(update_fields=["risk_score", "risk_category",
                                     "last_risk_update_at", "updated_at"])
        updated += 1
    return {"status": "ok", "districts_scored": updated,
            "duration_s": round(time.monotonic() - started, 2)}


@shared_task(bind=True, max_retries=2)
def generate_dss_recommendations(self):
    """Generate DSS recommendations for claims under review lacking recent ones."""
    started = time.monotonic()
    claims = FRAClaim.objects.filter(status=ClaimStatus.UNDER_REVIEW)
    total_recs = 0
    processed = 0
    for claim in claims.select_related("district"):
        recs = generate_and_store(claim)
        total_recs += len(recs)
        processed += 1
    return {"status": "ok", "claims_processed": processed,
            "recommendations_created": total_recs,
            "duration_s": round(time.monotonic() - started, 2)}


@shared_task(bind=True)
def compute_correlation_factors(self):
    """Recompute the Pearson correlation matrix from current snapshot factors."""
    started = time.monotonic()
    factors = ["Approval Rate", "Pending Claims Rate", "Avg Processing Time",
               "Forest Loss Rate", "Tribal Pop. Coverage", "CFR Recognition Rate",
               "Rejection Rate", "Encroachment Density"]
    series = {f: [] for f in factors}
    snaps = {}
    for s in DistrictRiskSnapshot.objects.order_by("prediction_timestamp"):
        snaps[s.district_id] = s  # newest wins
    for s in snaps.values():
        fj = s.factors_json or {}
        for f in factors:
            series[f].append(float(fj.get(f, 0.0)))

    def pearson(xs, ys):
        n = len(xs)
        if n < 2:
            return 0.0
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=False))
        dx = sum((a - mx) ** 2 for a in xs) ** 0.5
        dy = sum((b - my) ** 2 for b in ys) ** 0.5
        return round(num / (dx * dy), 4) if dx and dy else 0.0

    matrix = {a: {b: pearson(series[a], series[b]) for b in factors} for a in factors}
    FactorCorrelationMatrix.objects.create(
        matrix_json=matrix, method="pearson", factors=factors,
        sample_size=len(snaps),
    )
    return {"status": "ok", "factors": len(factors), "sample_size": len(snaps),
            "duration_s": round(time.monotonic() - started, 2)}


@shared_task(bind=True)
def refresh_materialized_views(self):
    """Refresh pre-computed aggregations (CONCURRENTLY on Postgres)."""
    from apps.analytics.matviews import refresh_all
    return {"status": "ok", **refresh_all()}


@shared_task(bind=True)
def monitor_prediction_drift(self):
    """Compare the live district risk-score distribution against the active
    model's training baseline (Population Stability Index). Flags drift so the
    model can be reviewed/retrained -- ML governance, not silent decay."""
    import statistics

    from apps.analytics.models import DistrictRiskSnapshot, RiskPredictionModel

    model = RiskPredictionModel.objects.filter(is_active=True).first()
    if not model:
        return {"status": "skipped", "reason": "no active model"}
    baseline = (model.training_metrics_json or {}).get("score_deciles")
    latest = {}
    for s in DistrictRiskSnapshot.objects.order_by("prediction_timestamp"):
        latest[s.district_id] = float(s.risk_score)
    scores = list(latest.values())
    if not scores:
        return {"status": "skipped", "reason": "no snapshots"}

    current_mean = round(statistics.fmean(scores), 2)
    drift = None
    if baseline:
        # PSI across fixed deciles of the training distribution
        import bisect
        edges = baseline
        def dist(vals):
            buckets = [0] * (len(edges) + 1)
            for v in vals:
                buckets[bisect.bisect_right(edges, v)] += 1
            n = len(vals) or 1
            return [b / n for b in buckets]
        cur = dist(scores)
        # baseline distribution is uniform-by-decile by construction (~0.1 each)
        base = [1 / (len(edges) + 1)] * (len(edges) + 1)
        psi = sum((c - b) * (__import__("math").log((c + 1e-6) / (b + 1e-6)))
                  for c, b in zip(cur, base, strict=False))
        drift = round(psi, 4)
    status = "DRIFT_DETECTED" if (drift is not None and drift > 0.2) else "ok"
    return {"status": status, "current_mean_risk": current_mean,
            "psi": drift, "n_districts": len(scores)}
