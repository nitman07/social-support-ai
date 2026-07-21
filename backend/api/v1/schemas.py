from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    role: str
    full_name: str | None


class ApplicantSummary(BaseModel):
    id: UUID
    full_name: str
    emirates_id: str
    nationality: str


class DocumentResponse(BaseModel):
    id: UUID
    document_type: str
    file_name: str
    ocr_status: str
    ocr_confidence: float | None


class AssessmentResponse(BaseModel):
    id: UUID
    ml_score: float | None
    ml_confidence: float | None
    decision: str
    llm_rationale: str | None
    decided_by: str | None


class InconsistencyResponse(BaseModel):
    id: UUID
    field: str
    source_a: str
    value_a: str
    source_b: str
    value_b: str
    severity: str
    status: str


class RecommendationResponse(BaseModel):
    id: UUID
    category: str
    title: str
    description: str | None
    relevance_score: float | None


class ApplicationListItem(BaseModel):
    id: UUID
    applicant_name: str
    status: str
    submitted_at: datetime | None
    created_at: datetime


class ApplicationDetail(BaseModel):
    id: UUID
    applicant: ApplicantSummary
    status: str
    workflow_id: str | None
    documents: list[DocumentResponse] = []
    assessment: AssessmentResponse | None
    inconsistencies: list[InconsistencyResponse] = []
    recommendations: list[RecommendationResponse] = []
    submitted_at: datetime | None
    created_at: datetime


class WorkflowStatusResponse(BaseModel):
    application_id: UUID
    status: str
    workflow_id: str | None
    decision: str | None
    ml_score: float | None
    requires_human_review: bool
    errors: list[str] = []


class ProcessResponse(BaseModel):
    application_id: UUID
    workflow_id: str
    status: str = "processing"
    message: str


class FlagResolveRequest(BaseModel):
    action: str = Field(..., pattern="^(accept|reject|flag_for_review)$")
    note: str | None = None


class SignoffRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|declined)$")
    rationale: str | None = None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationListItem]
    total: int
    page: int = 1
    page_size: int = 20
