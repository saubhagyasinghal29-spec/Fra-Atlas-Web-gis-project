"""Group fairness report for the risk model (ML governance).

Surfaces disparities in mean risk score and high-risk rate across states, so a
welfare-affecting model can be reviewed for systematic bias before it shapes
resource allocation. Read-only; informational.
"""
import statistics
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.analytics.models import DistrictRiskSnapshot


class Command(BaseCommand):
    help = "Report risk-score distribution by group (state) for bias review."

    def handle(self, *args, **opts):
        latest = {}
        for s in DistrictRiskSnapshot.objects.select_related("district").order_by("prediction_timestamp"):
            latest[s.district_id] = s
        by_state = defaultdict(list)
        for s in latest.values():
            by_state[s.district.state].append(float(s.risk_score))
        rows = []
        for state, scores in sorted(by_state.items()):
            rows.append((state, len(scores), round(statistics.fmean(scores), 1),
                         round(100 * sum(v >= 58 for v in scores) / len(scores), 1)))
        self.stdout.write("State | n | mean_risk | high_risk_%")
        for r in rows:
            self.stdout.write(f"  {r[0]:20s} {r[1]:3d}  {r[2]:5.1f}   {r[3]:5.1f}%")
        means = [r[2] for r in rows]
        if means:
            self.stdout.write(self.style.WARNING(
                f"Disparity (max-min mean risk across states): {round(max(means)-min(means),1)} points"))
