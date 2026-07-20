from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MLPrediction:
    score: float
    confidence: float
    feature_importance: dict[str, float]
    model_name: str


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    details: str | None = None


class IMLService(ABC):
    """Interface for ML model operations.

    Implementations use Scikit-learn (Random Forest) by default,
    but the interface supports any model class that provides
    predict_proba and feature_importance.
    """

    @abstractmethod
    async def predict(self, features: dict[str, float]) -> MLPrediction:
        """Run prediction on a feature vector and return score with explanation."""
        ...

    @abstractmethod
    async def predict_batch(self, features_list: list[dict[str, float]]) -> list[MLPrediction]:
        """Run batch predictions efficiently."""
        ...

    @abstractmethod
    async def get_feature_names(self) -> list[str]:
        """Return the list of expected feature names."""
        ...

    @abstractmethod
    async def evaluate_rules(self, features: dict[str, float]) -> list[RuleResult]:
        """Evaluate deterministic business rules against the feature set.

        Rules are applied BEFORE the ML model. If any hard rule fails,
        the application is routed accordingly without ML scoring.
        """
        ...

    @abstractmethod
    async def is_model_loaded(self) -> bool:
        """Check if the ML model is loaded and ready."""
        ...
