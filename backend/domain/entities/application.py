from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from backend.domain.entities.applicant import Applicant
from backend.core.exceptions import InvalidStateTransitionError, ApplicationAlreadySubmittedError


class ApplicationStatus(str, Enum):
    """Valid states for an application through its lifecycle."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    DECLINED = "declined"
    FAILED = "failed"

    def can_transition_to(self, target: "ApplicationStatus") -> bool:
        """Validate state transitions based on the status machine."""
        valid_transitions = {
            ApplicationStatus.DRAFT: {ApplicationStatus.SUBMITTED},
            ApplicationStatus.SUBMITTED: {ApplicationStatus.PROCESSING},
            ApplicationStatus.PROCESSING: {
                ApplicationStatus.AWAITING_REVIEW,
                ApplicationStatus.APPROVED,
                ApplicationStatus.DECLINED,
                ApplicationStatus.FAILED,
            },
            ApplicationStatus.AWAITING_REVIEW: {
                ApplicationStatus.PROCESSING,
                ApplicationStatus.APPROVED,
                ApplicationStatus.DECLINED,
            },
            ApplicationStatus.APPROVED: set(),
            ApplicationStatus.DECLINED: set(),
            ApplicationStatus.FAILED: {ApplicationStatus.SUBMITTED},
        }
        return target in valid_transitions.get(self, set())


@dataclass
class Application:
    """Aggregate root representing a social support application.

    Manages the application lifecycle through a strict status machine.
    Each application is associated with one applicant and tracks
    processing metadata including workflow execution state.
    """
    applicant_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: ApplicationStatus = ApplicationStatus.DRAFT
    workflow_id: str | None = None
    checkpoint_id: str | None = None
    metadata: dict | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def submit(self) -> None:
        """Transition from draft to submitted state."""
        if self.status == ApplicationStatus.SUBMITTED:
            raise ApplicationAlreadySubmittedError(str(self.id))
        self._transition_to(ApplicationStatus.SUBMITTED)
        self.submitted_at = datetime.now(timezone.utc)

    def start_processing(self, workflow_id: str) -> None:
        """Begin AI workflow processing."""
        self._transition_to(ApplicationStatus.PROCESSING)
        self.workflow_id = workflow_id

    def request_review(self, checkpoint_id: str) -> None:
        """Pause workflow for human-in-the-loop review."""
        self._transition_to(ApplicationStatus.AWAITING_REVIEW)
        self.checkpoint_id = checkpoint_id

    def resume_from_review(self) -> None:
        """Resume workflow after human review."""
        self._transition_to(ApplicationStatus.PROCESSING)
        self.checkpoint_id = None

    def approve(self) -> None:
        """Approve the application."""
        self._transition_to(ApplicationStatus.APPROVED)
        self.completed_at = datetime.now(timezone.utc)

    def decline(self) -> None:
        """Decline the application."""
        self._transition_to(ApplicationStatus.DECLINED)
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error: str | None = None) -> None:
        """Mark the application as failed due to a processing error."""
        self._transition_to(ApplicationStatus.FAILED)
        if error and self.metadata is not None:
            self.metadata["failure_reason"] = error
        elif error:
            self.metadata = {"failure_reason": error}

    def retry(self) -> None:
        """Retry a failed application (transition back to submitted)."""
        self._transition_to(ApplicationStatus.SUBMITTED)
        self.completed_at = None

    def _transition_to(self, target: ApplicationStatus) -> None:
        if not self.status.can_transition_to(target):
            raise InvalidStateTransitionError(
                application_id=str(self.id),
                current=self.status.value,
                target=target.value,
            )
        self.status = target
        self.updated_at = datetime.now(timezone.utc)
