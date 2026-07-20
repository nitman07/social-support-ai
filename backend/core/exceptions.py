from typing import Any


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(self.message)


class ApplicationError(DomainError):
    """Raised when an application operation fails."""


class ApplicationNotFoundError(ApplicationError):
    def __init__(self, application_id: str) -> None:
        super().__init__(
            message=f"Application {application_id} not found",
            context={"application_id": application_id},
        )


class InvalidStateTransitionError(ApplicationError):
    def __init__(self, application_id: str, current: str, target: str) -> None:
        super().__init__(
            message=f"Cannot transition application {application_id} from {current} to {target}",
            context={
                "application_id": application_id,
                "current_state": current,
                "target_state": target,
            },
        )


class ApplicationAlreadySubmittedError(ApplicationError):
    def __init__(self, application_id: str) -> None:
        super().__init__(
            message=f"Application {application_id} has already been submitted",
            context={"application_id": application_id},
        )


class DocumentError(DomainError):
    """Raised when a document operation fails."""


class DocumentNotFoundError(DocumentError):
    def __init__(self, document_id: str) -> None:
        super().__init__(
            message=f"Document {document_id} not found",
            context={"document_id": document_id},
        )


class UnsupportedDocumentTypeError(DocumentError):
    def __init__(self, document_type: str) -> None:
        super().__init__(
            message=f"Unsupported document type: {document_type}",
            context={"document_type": document_type},
        )


class DocumentProcessingError(DocumentError):
    def __init__(self, document_id: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to process document {document_id}: {reason}",
            context={"document_id": document_id, "reason": reason},
        )


class AgentError(DomainError):
    """Raised when an agent execution fails."""


class AgentExecutionError(AgentError):
    def __init__(self, agent_name: str, step: str, reason: str) -> None:
        super().__init__(
            message=f"Agent '{agent_name}' failed at step '{step}': {reason}",
            context={"agent_name": agent_name, "step": step, "reason": reason},
        )


class AgentMaxRetriesExceededError(AgentError):
    def __init__(self, agent_name: str, retries: int) -> None:
        super().__init__(
            message=f"Agent '{agent_name}' exceeded maximum retries ({retries})",
            context={"agent_name": agent_name, "retries": retries},
        )


class WorkflowError(DomainError):
    """Raised when a workflow execution fails."""


class WorkflowExecutionError(WorkflowError):
    def __init__(self, application_id: str, node: str, reason: str) -> None:
        super().__init__(
            message=f"Workflow for application {application_id} failed at node '{node}': {reason}",
            context={
                "application_id": application_id,
                "node": node,
                "reason": reason,
            },
        )


class ValidationError(DomainError):
    """Raised when data validation fails."""


class DataConsistencyError(ValidationError):
    def __init__(self, field: str, value_a: str, value_b: str, source_a: str, source_b: str) -> None:
        super().__init__(
            message=f"Data inconsistency in '{field}': '{value_a}' from {source_a} vs '{value_b}' from {source_b}",
            context={
                "field": field,
                "value_a": value_a,
                "value_b": value_b,
                "source_a": source_a,
                "source_b": source_b,
            },
        )


class MLError(DomainError):
    """Raised when ML model operations fail."""


class MLModelNotLoadedError(MLError):
    def __init__(self, model_path: str) -> None:
        super().__init__(
            message=f"ML model not loaded from {model_path}",
            context={"model_path": model_path},
        )


class MLPredictionError(MLError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"ML prediction failed: {reason}",
            context={"reason": reason},
        )


class LLMError(DomainError):
    """Raised when LLM service operations fail."""


class LLMServiceUnavailableError(LLMError):
    def __init__(self, host: str) -> None:
        super().__init__(
            message=f"LLM service unavailable at {host}",
            context={"host": host},
        )


class LLMResponseError(LLMError):
    def __init__(self, model: str, status_code: int, detail: str) -> None:
        super().__init__(
            message=f"LLM model '{model}' returned {status_code}: {detail}",
            context={"model": model, "status_code": status_code, "detail": detail},
        )


class ConfigurationError(DomainError):
    """Raised when configuration is invalid."""


class DatabaseConnectionError(DomainError):
    """Raised when a database connection fails."""

    def __init__(self, database: str, host: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to connect to {database} at {host}: {reason}",
            context={"database": database, "host": host, "reason": reason},
        )


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when authorization fails."""

    def __init__(self, user_id: str, required_role: str) -> None:
        super().__init__(
            message=f"User {user_id} lacks required role: {required_role}",
            context={"user_id": user_id, "required_role": required_role},
        )
