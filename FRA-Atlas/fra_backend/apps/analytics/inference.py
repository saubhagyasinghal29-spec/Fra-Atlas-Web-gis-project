"""Live risk inference.

RiskPredictor serves predictions from the ONNX artifact stored on the active
RiskPredictionModel row (real onnxruntime inference) and produces SHAP-based
explanations from the companion sklearn model. A small in-process cache keeps
the loaded model hot between calls; it is keyed on model version so deploying a
new version transparently invalidates it.

Feature set: the eight governance/forest factors carried on every
DistrictRiskSnapshot.factors_json. These are exactly what the model was trained
on, so feature assembly from the DB is consistent by construction. (The spec's
satellite features -- LST/NDVI/rainfall -- slot in here unchanged once that data
is ingested; only FEATURE_LIST and the training command change.)
"""
import hashlib
import io
import threading

import numpy as np

from apps.analytics.models import RiskPredictionModel, category_from_score

FEATURE_LIST = [
    "Approval Rate", "Pending Claims Rate", "Avg Processing Time",
    "Forest Loss Rate", "Tribal Pop. Coverage", "CFR Recognition Rate",
    "Rejection Rate", "Encroachment Density",
]

_CACHE = {}
_LOCK = threading.Lock()


class ModelNotAvailable(Exception):
    pass


class RiskPredictor:
    def __init__(self, *, version, feature_list, onnx_bytes, sklearn_model=None):
        import onnxruntime as ort

        self.version = version
        self.feature_list = feature_list
        self.session = ort.InferenceSession(
            onnx_bytes, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self._sklearn = sklearn_model  # for SHAP + per-tree confidence

    def _vectorize(self, features: dict) -> np.ndarray:
        row = []
        for name in self.feature_list:
            value = features.get(name)
            if value is None:
                raise ValueError(f"Missing feature '{name}'")
            row.append(float(value))
        return np.array([row], dtype=np.float32)

    def predict(self, features: dict) -> dict:
        x = self._vectorize(features)
        score = float(self.session.run(None, {self.input_name: x})[0].ravel()[0])
        score = max(0.0, min(100.0, score))
        confidence = self._confidence(x)
        return {
            "risk_score": round(score, 2),
            "risk_category": category_from_score(score),
            "confidence": round(confidence, 3),
            "model_version": self.version,
        }

    def _confidence(self, x: np.ndarray) -> float:
        """Inverse, normalized dispersion across the forest's trees.
        Tight agreement between trees -> high confidence."""
        if self._sklearn is None:
            return 0.8
        per_tree = np.array([est.predict(x)[0] for est in self._sklearn.estimators_])
        std = float(per_tree.std())
        return max(0.0, min(1.0, 1.0 - std / 25.0))

    def explain_prediction(self, features: dict, top_k: int = 5) -> dict:
        if self._sklearn is None:
            raise ModelNotAvailable("Explainer artifact unavailable for this model.")
        import shap

        x = self._vectorize(features)
        explainer = shap.TreeExplainer(self._sklearn)
        shap_values = np.array(explainer.shap_values(x)).reshape(len(self.feature_list))
        base = float(np.array(explainer.expected_value).ravel()[0])
        contribs = sorted(
            ({"feature": f, "value": float(features[f]), "shap": round(float(s), 3)}
             for f, s in zip(self.feature_list, shap_values, strict=False)),
            key=lambda d: abs(d["shap"]), reverse=True,
        )
        return {"base_value": round(base, 2), "top_factors": contribs[:top_k],
                "all_factors": contribs}


def get_active_predictor() -> RiskPredictor:
    model = RiskPredictionModel.objects.filter(is_active=True).order_by("-deployed_at").first()
    if not model or not model.model_binary_blob:
        raise ModelNotAvailable("No active model with an ONNX artifact is deployed.")
    with _LOCK:
        cached = _CACHE.get("predictor")
        if cached and cached.version == model.version:
            return cached
        sklearn_model = None
        if model.explainer_blob:
            import joblib
            sklearn_model = joblib.load(io.BytesIO(bytes(model.explainer_blob)))
        predictor = RiskPredictor(
            version=model.version, feature_list=model.feature_list or FEATURE_LIST,
            onnx_bytes=bytes(model.model_binary_blob), sklearn_model=sklearn_model,
        )
        _CACHE["predictor"] = predictor
        return predictor


def clear_predictor_cache():
    with _LOCK:
        _CACHE.pop("predictor", None)


def onnx_signature(onnx_bytes: bytes) -> str:
    return hashlib.sha256(onnx_bytes).hexdigest()
