"""The rule engine: deterministic, agronomy-driven scoring. No learning here.

Each crop is scored 0-100 by starting from a water-match score and applying
adjustments for groundwater sustainability, soil compatibility, season, and
temperature suitability. Every constant lives in CONFIG so the behaviour is
transparent and tunable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .knowledge_base import Crop
from .water import AvailableWater, available_water

# --- tunable scoring configuration -----------------------------------------

GROUNDWATER_BASE_PENALTY = {
    "safe": 0.0,
    "semi-critical": 10.0,
    "critical": 25.0,
    "over-exploited": 40.0,
}
# How strongly the groundwater penalty applies, by crop water intensity.
INTENSITY_FACTOR = {"low": 0.3, "medium": 0.7, "high": 1.0}

SOIL_GOOD_BONUS = 5.0
SOIL_POOR_PENALTY = -12.0
SEASON_MISMATCH_PENALTY = -50.0
TEMP_PENALTY_PER_DEGREE = 3.0
TEMP_PENALTY_CAP = 40.0


@dataclass(frozen=True)
class DistrictConditions:
    district: str
    rainfall_mm: float
    groundwater: str          # one of GROUNDWATER_BASE_PENALTY keys
    irrigation_pct: float     # 0..100
    soil: str                 # one of knowledge_base soil_types
    season: str               # rabi | kharif | zaid
    temperature_c: float      # representative growing-season mean temp

    def normalised(self) -> "DistrictConditions":
        return DistrictConditions(
            district=self.district,
            rainfall_mm=self.rainfall_mm,
            groundwater=self.groundwater.strip().lower(),
            irrigation_pct=self.irrigation_pct,
            soil=self.soil.strip().lower(),
            season=self.season.strip().lower(),
            temperature_c=self.temperature_c,
        )


@dataclass(frozen=True)
class CheckBreakdown:
    water_match: float
    groundwater_penalty: float
    soil_adjustment: float
    season_adjustment: float
    temperature_adjustment: float


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def water_match_score(avail: AvailableWater, crop: Crop) -> float:
    """100 when available water comfortably meets the crop's need; scales down
    linearly when it falls short. Surplus water is not penalised here (drainage
    is a soil concern, handled elsewhere)."""
    target = crop.water_target_mm
    if target <= 0:
        return 100.0
    return _clamp(avail.total_mm / target * 100.0)


def groundwater_penalty(cond: DistrictConditions, crop: Crop) -> float:
    base = GROUNDWATER_BASE_PENALTY.get(cond.groundwater)
    if base is None:
        raise ValueError(f"unknown groundwater status {cond.groundwater!r}")
    return base * INTENSITY_FACTOR[crop.intensity]


def soil_adjustment(cond: DistrictConditions, crop: Crop) -> float:
    return SOIL_GOOD_BONUS if cond.soil in crop.soils else SOIL_POOR_PENALTY


def season_adjustment(cond: DistrictConditions, crop: Crop) -> float:
    if crop.season == "annual" or crop.season == cond.season:
        return 0.0
    return SEASON_MISMATCH_PENALTY


def temperature_adjustment(cond: DistrictConditions, crop: Crop) -> float:
    """Zero inside the crop's suitable temperature band; a capped penalty
    proportional to how far outside it the district sits. This is what keeps a
    pan-India model from recommending a tropical crop in a cold district purely
    because the water matched."""
    t = cond.temperature_c
    if crop.temp_min_c <= t <= crop.temp_max_c:
        return 0.0
    degrees_outside = (crop.temp_min_c - t) if t < crop.temp_min_c else (t - crop.temp_max_c)
    return -min(TEMP_PENALTY_CAP, TEMP_PENALTY_PER_DEGREE * degrees_outside)


@dataclass(frozen=True)
class RuleResult:
    crop: Crop
    rule_score: float
    breakdown: CheckBreakdown


def score_crop(cond: DistrictConditions, crop: Crop, avail: AvailableWater) -> RuleResult:
    wm = water_match_score(avail, crop)
    gw = groundwater_penalty(cond, crop)
    soil = soil_adjustment(cond, crop)
    season = season_adjustment(cond, crop)
    temp = temperature_adjustment(cond, crop)
    rule = _clamp(wm - gw + soil + season + temp)
    return RuleResult(
        crop=crop,
        rule_score=rule,
        breakdown=CheckBreakdown(wm, gw, soil, season, temp),
    )


def score_all(cond: DistrictConditions, crops, avail: Optional[AvailableWater] = None):
    cond = cond.normalised()
    if avail is None:
        avail = available_water(cond.rainfall_mm, cond.irrigation_pct)
    return avail, [score_crop(cond, c, avail) for c in crops]
