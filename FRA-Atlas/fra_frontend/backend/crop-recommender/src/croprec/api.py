"""FastAPI service exposing the recommender.

Endpoints
    GET  /health                 liveness probe
    GET  /crops                  the knowledge base (what the engine knows)
    POST /recommend              one district  -> ranked, explained crops
    POST /recommend/batch        many districts -> map keyed by district
                                 (this is what the Web GIS choropleth consumes)

Run locally:
    pip install -r requirements.txt
    uvicorn croprec.api:app --reload --app-dir src
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import DistrictConditions, GROUNDWATER_BASE_PENALTY
from .knowledge_base import load_crops, soil_types
from .recommend import recommend

app = FastAPI(
    title="Pan-India Crop Recommender",
    version="0.1.0",
    description="Water-aware, sustainability-conscious crop recommendations.",
)

# The Web GIS frontend is typically served from a different origin in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConditionsIn(BaseModel):
    district: str = Field(..., examples=["Hisar (Haryana)"])
    rainfall_mm: float = Field(..., ge=0, examples=[450])
    groundwater: str = Field(..., examples=["critical"])
    irrigation_pct: float = Field(..., ge=0, le=100, examples=[55])
    soil: str = Field(..., examples=["sandy loam"])
    season: str = Field(..., examples=["rabi"])
    temperature_c: float = Field(..., examples=[22])

    def to_conditions(self) -> DistrictConditions:
        return DistrictConditions(
            district=self.district,
            rainfall_mm=self.rainfall_mm,
            groundwater=self.groundwater,
            irrigation_pct=self.irrigation_pct,
            soil=self.soil,
            season=self.season,
            temperature_c=self.temperature_c,
        )


class ReasonOut(BaseModel):
    ok: bool
    text: str


class CropOut(BaseModel):
    crop: str
    final_score: float
    rule_score: float
    ml_score: Optional[float]
    season: str
    water_target_mm: float
    reasons: List[ReasonOut]


class RecommendationOut(BaseModel):
    district: str
    available_water_mm: float
    effective_rain_mm: float
    irrigation_mm: float
    used_ml: bool
    recommendations: List[CropOut]


def _to_out(result) -> RecommendationOut:
    return RecommendationOut(
        district=result.district,
        available_water_mm=result.available_water_mm,
        effective_rain_mm=result.effective_rain_mm,
        irrigation_mm=result.irrigation_mm,
        used_ml=result.used_ml,
        recommendations=[
            CropOut(
                crop=r.crop,
                final_score=r.final_score,
                rule_score=r.rule_score,
                ml_score=r.ml_score,
                season=r.season,
                water_target_mm=r.water_target_mm,
                reasons=[ReasonOut(ok=ok, text=t) for ok, t in r.reasons],
            )
            for r in result.recommendations
        ],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "crops_loaded": len(load_crops())}


@app.get("/crops")
def crops() -> dict:
    return {
        "soil_types": soil_types(),
        "groundwater_levels": list(GROUNDWATER_BASE_PENALTY.keys()),
        "crops": [
            {
                "name": c.name,
                "season": c.season,
                "water_mm": [c.water_min_mm, c.water_max_mm],
                "intensity": c.intensity,
                "temp_c": [c.temp_min_c, c.temp_max_c],
                "soils": sorted(c.soils),
            }
            for c in load_crops()
        ],
    }


@app.post("/recommend", response_model=RecommendationOut)
def recommend_one(payload: ConditionsIn) -> RecommendationOut:
    return _to_out(recommend(payload.to_conditions()))


@app.post("/recommend/batch", response_model=Dict[str, RecommendationOut])
def recommend_batch(payload: List[ConditionsIn]) -> Dict[str, RecommendationOut]:
    """Score many districts at once. Returned keyed by district name so the GIS
    frontend can join each result straight onto its boundary polygon."""
    out: Dict[str, RecommendationOut] = {}
    for item in payload:
        out[item.district] = _to_out(recommend(item.to_conditions()))
    return out
