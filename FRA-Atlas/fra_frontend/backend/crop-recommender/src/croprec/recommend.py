"""recommend(): the single entry point that ties everything together.

This is the seam the ML layer and every frontend (Streamlit, FastAPI, the Web
GIS map) attach to. With no trained model present it returns pure rule-based
recommendations. Drop a model.joblib next to it and the same function blends in
ML probabilities -- nothing upstream changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .engine import DistrictConditions, score_all
from .explain import Reason, reasons_for
from .knowledge_base import Crop, load_crops
from .water import AvailableWater

DEFAULT_WEIGHTS = (0.6, 0.4)  # (rule, ml); see README for why this is tunable
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "model.joblib"


@dataclass
class CropRecommendation:
    crop: str
    final_score: float
    rule_score: float
    ml_score: Optional[float]
    reasons: List[Reason]
    season: str
    water_target_mm: float


@dataclass
class RecommendationResult:
    district: str
    available_water_mm: float
    effective_rain_mm: float
    irrigation_mm: float
    used_ml: bool
    recommendations: List[CropRecommendation] = field(default_factory=list)

    def top(self, n: int = 3) -> List[CropRecommendation]:
        return self.recommendations[:n]


# --- optional ML hook -------------------------------------------------------

def _load_model(path: Optional[Path]):
    """Return a loaded model or None. Never raises -- absence of ML is normal."""
    p = path or DEFAULT_MODEL_PATH
    if not Path(p).exists():
        return None
    try:
        import joblib  # noqa: WPS433  (optional dependency)
        return joblib.load(p)
    except Exception:
        return None


def _ml_probabilities(model, cond: DistrictConditions, crops: List[Crop]) -> Optional[Dict[str, float]]:
    if model is None:
        return None
    try:
        from .features import encode
        proba = model.predict_proba([encode(cond)])[0]
        classes = list(model.classes_)
        by_crop = {cls: float(p) for cls, p in zip(classes, proba)}
        return {c.name: by_crop.get(c.name, 0.0) for c in crops}
    except Exception:
        return None


# --- main entry point -------------------------------------------------------

def recommend(
    cond: DistrictConditions,
    *,
    crops: Optional[List[Crop]] = None,
    model=None,
    model_path: Optional[Path] = None,
    weights=DEFAULT_WEIGHTS,
    ml_scores: Optional[Dict[str, float]] = None,
) -> RecommendationResult:
    crops = crops if crops is not None else load_crops()
    cond = cond.normalised()

    avail, rule_results = score_all(cond, crops)

    if ml_scores is None:
        if model is None:
            model = _load_model(model_path)
        ml_scores = _ml_probabilities(model, cond, crops)

    used_ml = ml_scores is not None
    w_rule, w_ml = weights

    recs: List[CropRecommendation] = []
    for res in rule_results:
        ml_p = ml_scores.get(res.crop.name) if used_ml else None
        if used_ml and ml_p is not None:
            final = w_rule * res.rule_score + w_ml * (ml_p * 100.0)
        else:
            final = res.rule_score
        recs.append(CropRecommendation(
            crop=res.crop.name,
            final_score=round(final, 1),
            rule_score=round(res.rule_score, 1),
            ml_score=round(ml_p * 100.0, 1) if (used_ml and ml_p is not None) else None,
            reasons=reasons_for(cond, res, avail),
            season=res.crop.season,
            water_target_mm=res.crop.water_target_mm,
        ))

    recs.sort(key=lambda r: r.final_score, reverse=True)
    return RecommendationResult(
        district=cond.district,
        available_water_mm=round(avail.total_mm, 1),
        effective_rain_mm=round(avail.effective_rain_mm, 1),
        irrigation_mm=round(avail.irrigation_mm, 1),
        used_ml=used_ml,
        recommendations=recs,
    )
