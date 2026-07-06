"""Turn a crop's rule-engine breakdown into a list of plain-language reasons.

Each reason is (ok: bool, text). This is what makes the recommendation
trustworthy -- the user sees *why*, not just a number.
"""
from __future__ import annotations

from typing import List, Tuple

from .engine import RuleResult, DistrictConditions
from .water import AvailableWater

Reason = Tuple[bool, str]


def reasons_for(cond: DistrictConditions, res: RuleResult, avail: AvailableWater) -> List[Reason]:
    crop = res.crop
    b = res.breakdown
    out: List[Reason] = []

    if b.water_match >= 95:
        out.append((True, f"Water need met (~{crop.water_target_mm:.0f} mm, "
                          f"{avail.total_mm:.0f} mm available)"))
    elif b.water_match >= 60:
        out.append((False, f"Water a little short (needs ~{crop.water_target_mm:.0f} mm)"))
    else:
        out.append((False, f"Far too little water (needs ~{crop.water_target_mm:.0f} mm)"))

    if b.groundwater_penalty == 0:
        out.append((True, "Groundwater pressure low"))
    else:
        out.append((False, f"Penalised \u2212{b.groundwater_penalty:.0f}: "
                          f"{crop.intensity}-water crop in {cond.groundwater} block"))

    if b.soil_adjustment > 0:
        out.append((True, f"Soil suits it ({cond.soil})"))
    else:
        out.append((False, f"Not ideal for {cond.soil} soil"))

    if b.season_adjustment == 0:
        season_label = "all-season" if crop.season == "annual" else f"{cond.season} crop"
        out.append((True, f"Right season ({season_label})"))
    else:
        out.append((False, f"Wrong season (it is a {crop.season} crop)"))

    if b.temperature_adjustment == 0:
        out.append((True, f"Temperature suits it ({crop.temp_min_c:.0f}\u2013{crop.temp_max_c:.0f}\u00b0C)"))
    else:
        out.append((False, f"Temperature off ({cond.temperature_c:.0f}\u00b0C vs "
                          f"{crop.temp_min_c:.0f}\u2013{crop.temp_max_c:.0f}\u00b0C ideal)"))

    return out
