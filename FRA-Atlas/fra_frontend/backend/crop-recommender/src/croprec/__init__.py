"""croprec: a pan-India, water-aware, sustainability-conscious crop recommender.

Public API:
    from croprec import recommend, DistrictConditions
"""
from .engine import DistrictConditions
from .knowledge_base import Crop, load_crops, soil_types
from .recommend import (
    CropRecommendation,
    RecommendationResult,
    recommend,
)

__all__ = [
    "DistrictConditions",
    "Crop",
    "load_crops",
    "soil_types",
    "recommend",
    "CropRecommendation",
    "RecommendationResult",
]

__version__ = "0.1.0"
