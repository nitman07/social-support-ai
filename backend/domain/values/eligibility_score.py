from dataclasses import dataclass


@dataclass(frozen=True)
class EligibilityScore:
    """Value object representing an eligibility assessment score.

    Score ranges from 0.0 (ineligible) to 1.0 (fully eligible).
    Frozen to ensure the score and its metadata are immutable after creation.
    """
    score: float
    confidence: float
    feature_importance: dict[str, float] | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0 and 1: {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1: {self.confidence}")

    @property
    def is_eligible(self) -> bool:
        """Standard eligibility threshold. Configurable in production."""
        return self.score >= 0.5

    @property
    def is_high_confidence(self) -> bool:
        """High confidence threshold."""
        return self.confidence >= 0.8

    @property
    def needs_human_review(self) -> bool:
        """Borderline cases that need human decision."""
        return 0.4 <= self.score <= 0.6 or self.confidence < 0.6

    @property
    def top_features(self, n: int = 3) -> list[tuple[str, float]]:
        """Return top N features by importance."""
        if not self.feature_importance:
            return []
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        return sorted_features[:n]
