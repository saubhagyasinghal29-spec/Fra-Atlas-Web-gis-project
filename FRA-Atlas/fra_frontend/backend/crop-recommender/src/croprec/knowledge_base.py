"""Crop knowledge base: loads the agronomic crop table from data/crops.yaml.

This layer is pure lookup. It contains no learned parameters and no scoring
logic -- it just exposes the agronomic facts the rule engine reads.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "crops.yaml"

VALID_SEASONS = {"rabi", "kharif", "zaid", "annual"}
VALID_INTENSITY = {"low", "medium", "high"}


@dataclass(frozen=True)
class Crop:
    name: str
    season: str
    water_min_mm: float
    water_max_mm: float
    intensity: str
    temp_min_c: float
    temp_max_c: float
    soils: frozenset
    zones: tuple = field(default_factory=tuple)

    @property
    def water_target_mm(self) -> float:
        """Midpoint of the crop's seasonal water requirement range."""
        return (self.water_min_mm + self.water_max_mm) / 2.0


def _parse_crop(raw: dict) -> Crop:
    season = str(raw["season"]).strip().lower()
    intensity = str(raw["intensity"]).strip().lower()
    if season not in VALID_SEASONS:
        raise ValueError(f"{raw['name']}: invalid season {season!r}")
    if intensity not in VALID_INTENSITY:
        raise ValueError(f"{raw['name']}: invalid intensity {intensity!r}")
    water = raw["water_mm"]
    temp = raw["temp_c"]
    return Crop(
        name=str(raw["name"]).strip(),
        season=season,
        water_min_mm=float(water[0]),
        water_max_mm=float(water[1]),
        intensity=intensity,
        temp_min_c=float(temp[0]),
        temp_max_c=float(temp[1]),
        soils=frozenset(s.strip().lower() for s in raw["soils"]),
        zones=tuple(raw.get("zones", [])),
    )


@lru_cache(maxsize=1)
def load_crops(path: str | None = None) -> List[Crop]:
    """Load and validate the crop table. Cached; pass an explicit path to bypass."""
    p = Path(path) if path else DATA_FILE
    with open(p, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    crops = [_parse_crop(c) for c in doc["crops"]]
    if not crops:
        raise ValueError("crop knowledge base is empty")
    return crops


def soil_types(path: str | None = None) -> List[str]:
    p = Path(path) if path else DATA_FILE
    with open(p, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return [s.strip().lower() for s in doc.get("soil_types", [])]
