from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ApplicationSubmitted:
    application_id: UUID
    applicant_id: UUID
    document_count: int


@dataclass
class DocumentsUploaded:
    application_id: UUID
    document_ids: list[UUID]


@dataclass
class ProcessingStarted:
    application_id: UUID
    workflow_id: str


@dataclass
class OCRComplete:
    application_id: UUID
    document_id: UUID
    document_type: str
    confidence: float
    extracted_fields: dict[str, Any] | None = None


@dataclass
class ValidationComplete:
    application_id: UUID
    inconsistency_count: int
    requires_human_review: bool


@dataclass
class HumanReviewRequired:
    application_id: UUID
    checkpoint_id: str
    reason: str
    flags: list[dict[str, Any]] | None = None


@dataclass
class AssessmentComplete:
    application_id: UUID
    ml_score: float
    ml_confidence: float
    rule_results: list[dict[str, Any]] | None = None


@dataclass
class DecisionMade:
    application_id: UUID
    decision: str
    decision_source: str
    rationale: str | None = None
    recommendation_count: int = 0


@dataclass
class WorkflowFailed:
    application_id: UUID
    node: str
    error: str
    retry_count: int


@dataclass
class HumanActionTaken:
    application_id: UUID
    action: str
    user_id: str
    notes: str | None = None
