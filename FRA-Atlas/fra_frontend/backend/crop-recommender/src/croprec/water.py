"""Estimate effective water available to a crop in a district-season.

IMPORTANT (honesty note): the two coefficients below are simplifying
assumptions, not measured constants. They convert the supply side
(rainfall + irrigation cover) into a single millimetre figure comparable to
crop water requirements. In a production deployment these should be CALIBRATED
against real district data (NASA POWER effective rainfall, net irrigated area x
typical application depth) rather than left at these defaults.
"""
from __future__ import annotations

from dataclasses import dataclass

# Fraction of gross rainfall that is actually usable by the crop (the rest is
# lost to runoff, deep percolation and evaporation). FAO calls this effective
# rainfall; 0.7-0.8 is a common planning range.
EFFECTIVE_RAINFALL_FRACTION = 0.78

# Maximum supplemental water (mm) that full (100%) irrigation cover can add over
# a season. A coarse stand-in for canal + groundwater delivery capacity.
MAX_IRRIGATION_SUPPLEMENT_MM = 350.0


@dataclass(frozen=True)
class AvailableWater:
    total_mm: float
    effective_rain_mm: float
    irrigation_mm: float


def available_water(
    rainfall_mm: float,
    irrigation_cover_pct: float,
    *,
    eff_fraction: float = EFFECTIVE_RAINFALL_FRACTION,
    max_irrigation_mm: float = MAX_IRRIGATION_SUPPLEMENT_MM,
) -> AvailableWater:
    if rainfall_mm < 0:
        raise ValueError("rainfall_mm must be >= 0")
    if not 0 <= irrigation_cover_pct <= 100:
        raise ValueError("irrigation_cover_pct must be in [0, 100]")

    effective_rain = rainfall_mm * eff_fraction
    irrigation = (irrigation_cover_pct / 100.0) * max_irrigation_mm
    return AvailableWater(
        total_mm=effective_rain + irrigation,
        effective_rain_mm=effective_rain,
        irrigation_mm=irrigation,
    )
