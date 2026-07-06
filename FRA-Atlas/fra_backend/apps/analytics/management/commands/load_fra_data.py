"""Load the real FRA datasets shipped in seed_data/ into the database.

Populates:
  * geo.District               (name, state, denormalized latest risk)
  * analytics.DistrictRiskSnapshot  (risk index, PCA coords, cluster, factors)
  * analytics.RiskPredictionModel   (a v1.0.0 registry row matching the artifacts)
  * analytics.FactorCorrelationMatrix (Pearson correlations over the features CSV)
  * accounts role->permission grants

Usage:  python manage.py load_fra_data
"""
import csv
import statistics
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.bootstrap import seed_role_permissions
from apps.analytics.models import (
    DistrictRiskSnapshot,
    FactorCorrelationMatrix,
    RiskPredictionModel,
    category_from_level,
)
from apps.geo.geometry import generate_district_geometry
from apps.geo.models import District

RISK_CSV = "fra_risk_scores.csv"
FEATURES_CSV = "fra_features_500.csv"

FACTOR_COLUMNS = [
    "Approval Rate", "Pending Claims Rate", "Avg Processing Time",
    "Forest Loss Rate", "Tribal Pop. Coverage", "CFR Recognition Rate",
    "Rejection Rate", "Encroachment Density",
]

STATE_ABBR = {}


def state_code(state: str) -> str:
    words = state.split()
    if len(words) >= 2:
        abbr = "".join(w[0] for w in words[:3]).upper()
    else:
        abbr = state[:3].upper()
    STATE_ABBR[state] = abbr
    return abbr


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy), 4) if dx and dy else 0.0


class Command(BaseCommand):
    help = "Load real FRA risk + feature data into the database."

    @transaction.atomic
    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR) / "seed_data"
        now = timezone.now()

        grants = seed_role_permissions()
        self.stdout.write(f"Seeded {grants} role-permission grants.")

        model, _ = RiskPredictionModel.objects.update_or_create(
            version="1.0.0",
            defaults=dict(
                is_active=True, deployed_at=now, roc_auc=0.700, pr_auc=0.690,
                feature_list=FACTOR_COLUMNS,
                feature_importance_json={"note": "import ONNX artifact for real weights"},
            ),
        )

        # ---- districts + risk snapshots from the risk CSV ----
        per_state_counter = {}
        created_d = created_s = 0
        with open(base / RISK_CSV, newline="") as fh:
            for row in csv.DictReader(fh):
                state = row["state"].strip()
                abbr = state_code(state)
                per_state_counter[abbr] = per_state_counter.get(abbr, 0) + 1
                code = f"{abbr}-{per_state_counter[abbr]:03d}"

                factors = {c: _num(row.get(c)) for c in FACTOR_COLUMNS}
                category = category_from_level(row.get("Risk_Level"))
                risk_score = _num(row["Risk_Index"])

                geometry, centroid = generate_district_geometry(state, code)
                district, was_created = District.objects.update_or_create(
                    district_code=code,
                    defaults=dict(
                        name_english=row["district"].strip(), state=state,
                        risk_score=risk_score, risk_category=category,
                        last_risk_update_at=now,
                        geometry=geometry, centroid=centroid,
                    ),
                )
                created_d += int(was_created)
                DistrictRiskSnapshot.objects.create(
                    district=district, model_version=model.version,
                    risk_score=risk_score, risk_category=category,
                    risk_rank=int(_num(row.get("Risk_Rank")) or 0),
                    cluster=int(_num(row.get("Cluster")) or 0),
                    pc1=_num(row.get("PC1")), pc2=_num(row.get("PC2")),
                    factors_json=factors, prediction_timestamp=now,
                )
                created_s += 1
        self.stdout.write(f"Loaded {created_d} districts, {created_s} risk snapshots.")

        # ---- correlation matrix from the features CSV ----
        self._load_correlations(base / FEATURES_CSV, now)
        self.stdout.write(self.style.SUCCESS("FRA data load complete."))

    def _load_correlations(self, path, now):
        rows = list(csv.DictReader(open(path, newline="")))
        if not rows:
            return
        # derive comparable rates from raw counts
        series = {
            "approval_rate": [], "rejection_rate": [], "pending_rate": [],
            "avg_processing_days": [], "forest_loss_pct": [],
            "tribal_population_pct": [], "forest_cover_pct": [],
        }
        for r in rows:
            total = _num(r["TotalClaimsReceived"]) or 1
            series["approval_rate"].append(_num(r["ClaimsApproved"]) / total)
            series["rejection_rate"].append(_num(r["ClaimsRejected"]) / total)
            series["pending_rate"].append(_num(r["ClaimsPending"]) / total)
            series["avg_processing_days"].append(_num(r["AverageProcessingTime_Days"]))
            series["forest_loss_pct"].append(_num(r["ForestLoss_Percent"]))
            series["tribal_population_pct"].append(_num(r["TribalPopulation_Percent"]))
            series["forest_cover_pct"].append(_num(r["ForestCover_Percent"]))

        factors = list(series.keys())
        matrix = {a: {b: pearson(series[a], series[b]) for b in factors} for a in factors}
        FactorCorrelationMatrix.objects.create(
            matrix_json=matrix, method="pearson", factors=factors,
            sample_size=len(rows),
        )
        self.stdout.write(f"Computed {len(factors)}x{len(factors)} correlation matrix "
                          f"over {len(rows)} districts.")


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
