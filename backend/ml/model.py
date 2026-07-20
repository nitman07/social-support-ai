import pickle
from pathlib import Path

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier

from backend.core.config import settings
from backend.core.exceptions import MLModelNotLoadedError, MLPredictionError
from backend.core.logging import get_logger
from backend.domain.ports import IMLService, MLPrediction, RuleResult
from backend.ml.features import FEATURE_NAMES, FeatureVector
from backend.ml.rules import evaluate_all_rules

logger = get_logger(__name__)

MODEL_PATH = Path(settings.ml_model_path)


class MLService(IMLService):
    def __init__(self) -> None:
        self._model: RandomForestClassifier | None = None
        self._explainer: shap.TreeExplainer | None = None

    async def load_model(self) -> None:
        if not MODEL_PATH.exists():
            logger.warning(f"Model not found at {MODEL_PATH}, predictions will not be available")
            return
        with open(MODEL_PATH, "rb") as f:
            self._model = pickle.load(f)
        self._explainer = shap.TreeExplainer(self._model)
        logger.info(f"Model loaded from {MODEL_PATH}")

    def _extract_shap(self, shap_values: np.ndarray) -> np.ndarray:
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        while shap_values.ndim > 2:
            shap_values = shap_values[:, :, 1]
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(1, -1)
        return shap_values

    async def predict(self, features: dict[str, float]) -> MLPrediction:
        if self._model is None:
            raise MLModelNotLoadedError(str(MODEL_PATH))

        try:
            X = np.array([[features[name] for name in FEATURE_NAMES]])
            proba = self._model.predict_proba(X)[0]
            score = float(proba[1])
            confidence = float(max(proba))

            feature_importance = {}
            if self._explainer is not None:
                sv = self._explainer.shap_values(X)
                sv = self._extract_shap(sv)
                for i, name in enumerate(FEATURE_NAMES):
                    feature_importance[name] = round(float(sv[0, i]), 6)

            return MLPrediction(
                score=round(score, 4),
                confidence=round(confidence, 4),
                feature_importance=feature_importance,
                model_name="RandomForest",
            )
        except Exception as e:
            raise MLPredictionError(str(e))

    async def predict_batch(self, features_list: list[dict[str, float]]) -> list[MLPrediction]:
        if self._model is None:
            raise MLModelNotLoadedError(str(MODEL_PATH))

        try:
            X = np.array([[f[name] for name in FEATURE_NAMES] for f in features_list])
            proba = self._model.predict_proba(X)
            scores = proba[:, 1]
            confidences = np.max(proba, axis=1)

            sv = None
            if self._explainer is not None:
                sv = self._explainer.shap_values(X)
                sv = self._extract_shap(sv)

            results = []
            for i in range(len(features_list)):
                fi = {}
                if sv is not None:
                    for j, name in enumerate(FEATURE_NAMES):
                        fi[name] = round(float(sv[i, j]), 6)

                results.append(MLPrediction(
                    score=round(float(scores[i]), 4),
                    confidence=round(float(confidences[i]), 4),
                    feature_importance=fi,
                    model_name="RandomForest",
                ))
            return results
        except Exception as e:
            raise MLPredictionError(str(e))

    async def get_feature_names(self) -> list[str]:
        return list(FEATURE_NAMES)

    async def evaluate_rules(self, features: dict[str, float]) -> list[RuleResult]:
        return await evaluate_all_rules(features)

    async def is_model_loaded(self) -> bool:
        return self._model is not None


ml_service = MLService()
