"""Predictive-analytics persistence.

This build ships the *registry and snapshot* layer (versioned model metadata,
per-district risk snapshots, correlation matrix) populated from the real
fra_risk_scores dataset. Live ONNX inference + SHAP is the next slice; the
RiskPredictionModel row already carries the binary blob + signature columns it
will use, and analytics/inference.py documents the interface.
"""

from django.db import models

from apps.common.enums import RiskCategory
from apps.common.models import BaseModel
from apps.geo.models import District


class RiskPredictionModel(BaseModel):
    version = models.CharField(max_length=32, unique=True)  # semver, e.g. "1.0.0"
    deployed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    roc_auc = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    pr_auc = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    feature_importance_json = models.JSONField(default=dict, blank=True)
    feature_list = models.JSONField(default=list, blank=True)
    model_binary_blob = models.BinaryField(null=True, blank=True)  # ONNX bytes (serving)
    explainer_blob = models.BinaryField(null=True, blank=True)     # joblib sklearn model (SHAP)
    signature_sha256 = models.CharField(max_length=64, blank=True, default="")
    training_metrics_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "risk_prediction_model"

    def __str__(self):
        return f"RiskModel v{self.version}{' (active)' if self.is_active else ''}"


class DistrictRiskSnapshot(BaseModel):
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="risk_snapshots"
    )
    model_version = models.CharField(max_length=32, blank=True, default="")
    risk_score = models.DecimalField(max_digits=6, decimal_places=2)
    risk_category = models.CharField(max_length=16, choices=RiskCategory.choices)
    risk_rank = models.PositiveIntegerField(null=True, blank=True)
    cluster = models.IntegerField(null=True, blank=True)
    pc1 = models.FloatField(null=True, blank=True)
    pc2 = models.FloatField(null=True, blank=True)
    factors_json = models.JSONField(default=dict, blank=True)
    shap_explanation_json = models.JSONField(default=dict, blank=True)
    prediction_timestamp = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "district_risk_snapshot"
        indexes = [models.Index(fields=["district", "prediction_timestamp"])]


class FactorCorrelationMatrix(BaseModel):
    matrix_json = models.JSONField()
    method = models.CharField(max_length=16, default="pearson")
    factors = models.JSONField(default=list)
    sample_size = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "factor_correlation_matrix"


def category_from_level(level: str) -> str:
    """Map the dataset's 4-level scheme onto the RiskCategory enum by rank:
    Critical > Moderate > Good > Excellent  ->  CRITICAL > HIGH > MODERATE > LOW.
    """
    return {
        "Critical": RiskCategory.CRITICAL,
        "Moderate": RiskCategory.HIGH,
        "Good": RiskCategory.MODERATE,
        "Excellent": RiskCategory.LOW,
        # also accept enum-style labels if a future dataset uses them
        "High": RiskCategory.HIGH,
        "Low": RiskCategory.LOW,
    }.get((level or "").strip(), RiskCategory.MODERATE)


def category_from_score(score: float) -> str:
    """Thresholds derived from the observed Risk_Index distribution per level."""
    if score >= 58:
        return RiskCategory.CRITICAL
    if score >= 48:
        return RiskCategory.HIGH
    if score >= 38:
        return RiskCategory.MODERATE
    return RiskCategory.LOW
