"""Feature encoding shared by training (train.py) and inference (recommend.py).

Keeping this in ONE place is deliberate: the #1 way ML systems silently break is
features being computed differently at train time and serve time. Both paths
import from here, so they cannot drift.
"""
from __future__ import annotations

from typing import Dict, List

from .engine import DistrictConditions, GROUNDWATER_BASE_PENALTY

# Stable, ordered category lists. Order defines column positions in the vector.
GROUNDWATER_LEVELS = ["safe", "semi-critical", "critical", "over-exploited"]
SOIL_LEVELS = ["sandy", "sandy loam", "loam", "clay loam", "clay"]
SEASON_LEVELS = ["rabi", "kharif", "zaid", "annual"]


def feature_names() -> List[str]:
    names = ["rainfall_mm", "irrigation_pct", "temperature_c", "groundwater_ordinal"]
    names += [f"soil={s}" for s in SOIL_LEVELS]
    names += [f"season={s}" for s in SEASON_LEVELS]
    return names


def encode(cond: DistrictConditions) -> List[float]:
    """Encode district conditions into a fixed-length numeric feature vector."""
    c = cond.normalised()
    gw_ord = float(GROUNDWATER_LEVELS.index(c.groundwater)) if c.groundwater in GROUNDWATER_LEVELS else -1.0
    vec: List[float] = [
        float(c.rainfall_mm),
        float(c.irrigation_pct),
        float(c.temperature_c),
        gw_ord,
    ]
    vec += [1.0 if c.soil == s else 0.0 for s in SOIL_LEVELS]
    vec += [1.0 if c.season == s else 0.0 for s in SEASON_LEVELS]
    return vec
