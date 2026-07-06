"""Decision Support engine.

Given an FRA claim, derives welfare-scheme recommendations from its district's
latest risk snapshot. Rules are data-aware (the real Risk_Index tops out ~77 and
'Tribal Pop. Coverage' is a 0-1 fraction), and each recommendation carries a
confidence in [0,1] plus the supporting factor values that triggered it.

This is a transparent rule engine by design: in a welfare context, officers must
be able to see *why* a scheme was suggested. The ML risk score feeds the rules;
the rules themselves stay auditable.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.analytics.models import DistrictRiskSnapshot
from apps.claims.models import DSSRecommendation, FRAClaim


def _latest_snapshot(district):
    return (DistrictRiskSnapshot.objects.filter(district=district)
            .order_by("-prediction_timestamp").first())


def evaluate_claim(claim: FRAClaim) -> list[dict]:
    """Return a list of recommendation dicts (not persisted)."""
    snap = _latest_snapshot(claim.district)
    if not snap:
        return []
    f = snap.factors_json or {}
    score = float(snap.risk_score)
    recs = []

    def add(rtype, confidence, factors):
        recs.append({
            "recommendation_type": rtype,
            "confidence_score": round(min(max(confidence, 0.0), 1.0), 3),
            "supporting_factors": factors,
        })

    # 1. High ecological risk -> forest management + habitat protection
    if score >= 58 or f.get("Forest Loss Rate", 0) >= 1.5:
        conf = 0.6 + min(score, 80) / 200 + min(f.get("Forest Loss Rate", 0), 3) / 10
        add("FOREST_MANAGEMENT", conf,
            [{"risk_score": score}, {"forest_loss_rate": f.get("Forest Loss Rate")}])
        add("HABITAT_PROTECTION", conf - 0.05,
            [{"risk_category": snap.risk_category}])

    # 2. Weak tribal coverage -> direct income + livelihood support
    coverage = f.get("Tribal Pop. Coverage", 1.0)
    if coverage < 0.05:
        add("PM_KISAN", 0.55 + (0.05 - coverage) * 6,
            [{"tribal_pop_coverage": coverage}])
        add("LIVELIHOOD_SUPPORT", 0.5 + (0.05 - coverage) * 5,
            [{"tribal_pop_coverage": coverage}])

    # 3. Administrative bottleneck -> process acceleration
    approval = f.get("Approval Rate", 1.0)
    pending = f.get("Pending Claims Rate", 0.0)
    proc_days = f.get("Avg Processing Time", 0.0)
    if approval < 0.45 or pending > 0.4 or proc_days > 110:
        conf = 0.5 + (0.45 - min(approval, 0.45)) + min(pending, 0.5) / 2
        add("PROCESS_ACCELERATION", conf,
            [{"approval_rate": approval}, {"pending_rate": pending},
             {"avg_processing_days": proc_days}])

    # 4. Baseline employment guarantee if nothing stronger fired
    if not recs:
        add("MGNREGA", 0.5, [{"baseline": True}])

    return recs


@transaction.atomic
def generate_and_store(claim: FRAClaim, *, stale_after_days: int = 7) -> list[DSSRecommendation]:
    """Persist recommendations for a claim, skipping if recent ones exist."""
    cutoff = timezone.now() - timezone.timedelta(days=stale_after_days)
    if DSSRecommendation.objects.filter(fra_claim=claim, created_at__gte=cutoff).exists():
        return list(DSSRecommendation.objects.filter(fra_claim=claim))

    created = []
    summary = []
    for rec in evaluate_claim(claim):
        obj = DSSRecommendation.objects.create(
            fra_claim=claim,
            recommendation_type=rec["recommendation_type"],
            confidence_score=Decimal(str(rec["confidence_score"])),
            supporting_factors=rec["supporting_factors"],
        )
        created.append(obj)
        summary.append({"type": obj.recommendation_type,
                        "confidence": float(obj.confidence_score)})
    # cache latest summary on the claim for quick reads
    claim.dss_recommendations_json = {"generated_at": timezone.now().isoformat(),
                                      "recommendations": summary}
    claim.save(update_fields=["dss_recommendations_json", "updated_at"])
    return created
