from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events.

    Every event carries a unique ID, timestamp, and optional correlation
    ID for tracing across service boundaries.
    """
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None


@dataclass
class ApplicationSubmitted(DomainEvent):
    """Published when an applicant submits their application."""
    application_id: UUID
    applicant_id: UUID
    document_count: int


@dataclass
class DocumentsUploaded(DomainEvent):
    """Published when documents are uploaded to an application."""
    application_id: UUID
    document_ids: list[UUID]


@dataclass
class ProcessingStarted(DomainEvent):
    """Published when the AI workflow begins processing."""
    application_id: UUID
    workflow_id: str


@dataclass
class OCRComplete(DomainEvent):
    """Published when OCR processing finishes for a document."""
    application_id: UUID
    document_id: UUID
    document_type: str
    confidence: float
    extracted_fields: dict[str, Any] | None = None


@dataclass
class ValidationComplete(DomainEvent):
    """Published when cross-validation of extracted data finishes."""
    application_id: UUID
    inconsistency_count: int
    requires_human_review: bool


@dataclass
class HumanReviewRequired(DomainEvent):
    """Published when the workflow reaches a human-in-the-loop checkpoint."""
    application_id: UUID
    checkpoint_id: str
    reason: str
    flags: list[dict[str, Any]] | None = None


@dataclass
class AssessmentComplete(DomainEvent):
    """Published when eligibility assessment finishes."""
    application_id: UUID
    ml_score: float
    ml_confidence: float
    rule_results: list[dict[str, Any]] | None = None


@dataclass
class DecisionMade(DomainEvent):
    """Published when a final decision is rendered."""
    application_id: UUID
    decision: str  # approved | soft_decline | referred
    decision_source: str  # system | human_reviewer
    rationale: str | None = None
    recommendation_count: int = 0


@dataclass
class WorkflowFailed(DomainEvent):
    """Published when the workflow encounters an unrecoverable error."""
    application_id: UUID
    node: str
    error: str
    retry_count: int


@dataclass
class HumanActionTaken(DomainEvent):
    """Published when a human reviewer takes action on a checkpoint."""
    application_id: UUID
    action: str
    user_id: str
    notes: str | None = None
