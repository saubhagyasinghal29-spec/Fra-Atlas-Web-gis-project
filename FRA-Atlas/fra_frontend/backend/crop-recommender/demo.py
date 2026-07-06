"""Worked pan-India examples. Run: python demo.py

Demonstrates that the SAME engine handles districts from very different
agro-climatic zones, with no model and no per-state hardcoding.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from croprec import DistrictConditions, recommend  # noqa: E402

EXAMPLES = [
    DistrictConditions("Hisar (Haryana)", rainfall_mm=450, groundwater="critical",
                       irrigation_pct=55, soil="sandy loam", season="rabi", temperature_c=22),
    DistrictConditions("Ludhiana (Punjab)", rainfall_mm=700, groundwater="over-exploited",
                       irrigation_pct=98, soil="loam", season="kharif", temperature_c=31),
    DistrictConditions("Barmer (Rajasthan)", rainfall_mm=270, groundwater="semi-critical",
                       irrigation_pct=20, soil="sandy", season="kharif", temperature_c=33),
    DistrictConditions("Bardhaman (West Bengal)", rainfall_mm=1400, groundwater="safe",
                       irrigation_pct=70, soil="clay loam", season="kharif", temperature_c=29),
    DistrictConditions("Tumkur (Karnataka)", rainfall_mm=600, groundwater="critical",
                       irrigation_pct=35, soil="loam", season="kharif", temperature_c=26),
]


def show(cond: DistrictConditions) -> None:
    result = recommend(cond)
    print(f"\n=== {result.district} ===")
    print(f"  season={cond.season}  soil={cond.soil}  groundwater={cond.groundwater}  "
          f"temp={cond.temperature_c:.0f}C")
    print(f"  available water = {result.available_water_mm:.0f} mm "
          f"({result.effective_rain_mm:.0f} rain + {result.irrigation_mm:.0f} irrigation) "
          f"| ML used: {result.used_ml}")
    for i, r in enumerate(result.top(4), 1):
        print(f"  {i}. {r.crop:<22} score={r.final_score:>5.1f}  (rule={r.rule_score:.0f})")
    worst = result.recommendations[-1]
    print(f"     ...lowest: {worst.crop} ({worst.final_score:.0f})  "
          f"-> {[t for ok, t in worst.reasons if not ok][:1]}")


if __name__ == "__main__":
    for ex in EXAMPLES:
        show(ex)
    print()
