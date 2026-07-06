"""Train the district-risk model on the real dataset and register it.

Trains a RandomForest regressor (Risk_Index from the 8 governance/forest
factors), exports it to ONNX for serving, pickles the sklearn model for SHAP,
and writes a versioned, signed RiskPredictionModel row marked active.

Note on metrics: Risk_Index in the dataset is a composite of these 8 factors,
so the model recovers the scoring function (R^2 ~ 0.92). This validates the
full train -> ONNX -> serve -> explain pipeline end to end. The spec's ~0.70
ROC-AUC refers to the satellite-feature fire-risk model (LST/NDVI/rainfall),
which drops into the same pipeline once that data is ingested.

Usage:  python manage.py train_risk_model [--model-version 1.1.0]
"""
import csv
import io
from pathlib import Path

import joblib
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from skl2onnx import to_onnx
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

from apps.analytics.inference import FEATURE_LIST, clear_predictor_cache, onnx_signature
from apps.analytics.models import RiskPredictionModel


class Command(BaseCommand):
    help = "Train and register the district risk model (ONNX + SHAP)."

    def add_arguments(self, parser):
        parser.add_argument("--model-version", default="1.0.0")
        parser.add_argument("--csv", default="fra_risk_scores.csv")

    def handle(self, *args, **opts):
        path = Path(settings.BASE_DIR) / "seed_data" / opts["csv"]
        rows = list(csv.DictReader(open(path, newline="")))
        X = np.array([[float(r[c]) for c in FEATURE_LIST] for r in rows], dtype=np.float32)
        y = np.array([float(r["Risk_Index"]) for r in rows], dtype=np.float32)

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
        model.fit(X_tr, y_tr)
        r2 = float(r2_score(y_te, model.predict(X_te)))
        # drift baseline: deciles of the training-set predictions (for PSI)
        import numpy as _np
        preds_all = model.predict(X)
        score_deciles = [round(float(q), 3) for q in _np.quantile(preds_all, _np.arange(0.1, 1.0, 0.1))]
        # 5-fold CV for honest generalization estimate
        from sklearn.model_selection import cross_val_score
        cv = cross_val_score(model, X, y, cv=5, scoring="r2")

        onnx_bytes = to_onnx(model, X[:1]).SerializeToString()
        explainer_bytes = io.BytesIO()
        joblib.dump(model, explainer_bytes)

        importances = {f: round(float(v), 4)
                       for f, v in zip(FEATURE_LIST, model.feature_importances_, strict=False)}

        RiskPredictionModel.objects.filter(is_active=True).exclude(
            version=opts["model_version"]).update(is_active=False)
        rm, _ = RiskPredictionModel.objects.update_or_create(
            version=opts["model_version"],
            defaults=dict(
                is_active=True, deployed_at=timezone.now(),
                roc_auc=None, pr_auc=None,
                feature_list=FEATURE_LIST, feature_importance_json=importances,
                model_binary_blob=onnx_bytes, explainer_blob=explainer_bytes.getvalue(),
                signature_sha256=onnx_signature(onnx_bytes),
                training_metrics_json={
                    "r2_test": round(r2, 4), "r2_cv_mean": round(float(cv.mean()), 4),
                    "r2_cv_std": round(float(cv.std()), 4), "n_samples": len(rows),
                    "algorithm": "RandomForestRegressor(n=200, depth=8)",
                    "target": "Risk_Index", "score_deciles": score_deciles,
                    "note": "Risk_Index is a composite of the inputs; R2 validates the "
                    "serving pipeline, not novel predictive lift.",
                },
            ),
        )
        clear_predictor_cache()
        self.stdout.write(self.style.SUCCESS(
            f"Registered model v{rm.version}: R2(test)={r2:.3f}, "
            f"sig={rm.signature_sha256[:12]}..., active=True"
        ))
        top = sorted(importances.items(), key=lambda kv: -kv[1])[:3]
        self.stdout.write("Top factors: " + ", ".join(f"{k}={v}" for k, v in top))
