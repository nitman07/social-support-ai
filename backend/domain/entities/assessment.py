from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from backend.domain.values.eligibility_score import EligibilityScore


class Decision(str, Enum):
    APPROVED = "approved"
    SOFT_DECLINE = "soft_decline"
    REFERRED = "referred"
    PENDING = "pending"


class DecisionSource(str, Enum):
    SYSTEM = "system"
    HUMAN_REVIEWER = "human_reviewer"


@dataclass
class Assessment:
    """Entity representing the outcome of an application assessment.

    Combines ML prediction, LLM rationale, and final decision.
    Every assessment produces an audit trail for compliance.
    """
    application_id: UUID
    eligibility_score: EligibilityScore | None = None
    llm_rationale: str | None = None
    decision: Decision = Decision.PENDING
    decision_source: DecisionSource = DecisionSource.SYSTEM
    id: UUID = field(default_factory=uuid4)
    decided_by: str | None = None
    decided_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_ml_result(self, score: EligibilityScore) -> None:
        self.eligibility_score = score

    def record_llm_rationale(self, rationale: str) -> None:
        self.llm_rationale = rationale

    def approve(self, decided_by: str = "system") -> None:
        self.decision = Decision.APPROVED
        self.decision_source = DecisionSource.SYSTEM if decided_by == "system" else DecisionSource.HUMAN_REVIEWER
        self.decided_by = decided_by
        self.decided_at = datetime.now(timezone.utc)

    def soft_decline(self, decided_by: str = "system") -> None:
        self.decision = Decision.SOFT_DECLINE
        self.decision_source = DecisionSource.SYSTEM if decided_by == "system" else DecisionSource.HUMAN_REVIEWER
        self.decided_by = decided_by
        self.decided_at = datetime.now(timezone.utc)

    def refer_to_human(self, decided_by: str = "system") -> None:
        self.decision = Decision.REFERRED
        self.decision_source = DecisionSource.SYSTEM
        self.decided_by = decided_by
        self.decided_at = datetime.now(timezone.utc)
