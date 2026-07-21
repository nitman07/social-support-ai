from typing import Any, Optional

from typing_extensions import TypedDict


class DocumentInfo(TypedDict):
    id: str
    document_type: str
    file_name: str
    ocr_status: str
    ocr_confidence: float


class Inconsistency(TypedDict):
    field: str
    source_a: str
    value_a: str
    source_b: str
    value_b: str
    severity: str


class PolicyContext(TypedDict):
    id: str
    title: str
    content: str
    relevance_score: float


class RuleResult(TypedDict):
    rule_name: str
    passed: bool
    details: Optional[str]


class Recommendation(TypedDict):
    category: str
    title: str
    description: str
    relevance_score: float


class ApplicationState(TypedDict):
    application_id: str
    applicant_id: str
    status: str
    workflow_id: str

    documents: list[DocumentInfo]
    ocr_results: dict[str, Any]
    extraction_complete: bool

    validated_data: dict[str, Any]
    inconsistencies: list[Inconsistency]
    validation_complete: bool
    requires_human_review: bool

    retrieved_policies: list[PolicyContext]

    ml_features: dict[str, float]
    ml_score: Optional[float]
    ml_confidence: Optional[float]
    ml_feature_importance: dict[str, float]
    eligibility_rules_applied: list[RuleResult]

    decision: Optional[str]
    decision_rationale: Optional[str]
    decision_confidence: float

    recommendations: list[Recommendation]

    errors: list[str]
    retry_count: int
