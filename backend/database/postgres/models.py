import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.postgres.database import Base


class ApplicantModel(Base):
    __tablename__ = "applicants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    emirates_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    passport_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    nationality: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    applications: Mapped[list["ApplicationModel"]] = relationship(
        back_populates="applicant", lazy="selectin"
    )


class ApplicationModel(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="draft", index=True
    )
    workflow_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checkpoint_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    app_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    applicant: Mapped["ApplicantModel"] = relationship(back_populates="applications")
    documents: Mapped[list["DocumentModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["AssessmentModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    income_records: Mapped[list["ExtractedIncomeModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    employment_records: Mapped[list["ExtractedEmploymentModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    family_members: Mapped[list["FamilyMemberModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    assets: Mapped[list["ExtractedAssetModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    liabilities: Mapped[list["ExtractedLiabilityModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    inconsistencies: Mapped[list["InconsistencyModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        back_populates="application", lazy="selectin", cascade="all, delete-orphan"
    )


class DocumentModel(Base):
    __tablename__ = "application_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(30), default="pending")
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="documents")


class AssessmentModel(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    ml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    llm_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(30), default="pending")
    decision_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="assessments")
    recommendations: Mapped[list["RecommendationModel"]] = relationship(
        back_populates="assessment", lazy="selectin", cascade="all, delete-orphan"
    )


class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rec_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    assessment: Mapped["AssessmentModel"] = relationship(back_populates="recommendations")


class ExtractedIncomeModel(Base):
    __tablename__ = "extracted_income"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="AED")
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="income_records")


class ExtractedEmploymentModel(Base):
    __tablename__ = "extracted_employment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    employer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="employment_records")


class FamilyMemberModel(Base):
    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_dependent: Mapped[bool] = mapped_column(Boolean, default=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="family_members")


class ExtractedAssetModel(Base):
    __tablename__ = "extracted_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="assets")


class ExtractedLiabilityModel(Base):
    __tablename__ = "extracted_liabilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    liability_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_payment: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="liabilities")


class InconsistencyModel(Base):
    __tablename__ = "inconsistencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True
    )
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    source_a: Mapped[str] = mapped_column(String(100), nullable=False)
    value_a: Mapped[str] = mapped_column(Text, nullable=False)
    source_b: Mapped[str] = mapped_column(String(100), nullable=False)
    value_b: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="open")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="inconsistencies")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    application: Mapped["ApplicationModel"] = relationship(back_populates="audit_logs")


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
