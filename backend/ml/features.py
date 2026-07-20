import math
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.postgres import (
    ApplicantModel,
    ApplicationModel,
    AssessmentModel,
    DocumentModel,
    ExtractedAssetModel,
    ExtractedEmploymentModel,
    ExtractedIncomeModel,
    ExtractedLiabilityModel,
    FamilyMemberModel,
    InconsistencyModel,
    async_session_factory,
)

logger = get_logger(__name__)

FEATURE_NAMES = [
    "monthly_income",
    "family_size",
    "years_employed",
    "total_assets",
    "total_liabilities",
    "liability_to_income_ratio",
    "has_inconsistencies",
    "num_documents",
]


@dataclass
class FeatureVector:
    application_id: UUID
    features: dict[str, float]
    label: float | None = None

    @property
    def array(self) -> list[float]:
        return [self.features[name] for name in FEATURE_NAMES]


async def extract_features_for_application(application_id: UUID) -> FeatureVector | None:
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if app is None:
            return None

        features: dict[str, float] = {}

        income = await session.execute(
            select(func.coalesce(func.sum(ExtractedIncomeModel.amount), 0.0))
            .where(ExtractedIncomeModel.application_id == application_id)
        )
        features["monthly_income"] = float(income.scalar() or 0.0)

        family_count = await session.execute(
            select(func.count(FamilyMemberModel.id))
            .where(FamilyMemberModel.application_id == application_id)
        )
        features["family_size"] = int(family_count.scalar() or 0)

        emp = await session.execute(
            select(ExtractedEmploymentModel.start_date)
            .where(ExtractedEmploymentModel.application_id == application_id)
            .limit(1)
        )
        emp_row = emp.first()
        if emp_row and emp_row[0]:
            delta = datetime.now(timezone.utc).date() - emp_row[0]
            features["years_employed"] = round(max(0.0, delta.days / 365.0), 2)
        else:
            features["years_employed"] = 0.0

        assets = await session.execute(
            select(func.coalesce(func.sum(ExtractedAssetModel.value), 0.0))
            .where(ExtractedAssetModel.application_id == application_id)
        )
        features["total_assets"] = float(assets.scalar() or 0.0)

        liabilities = await session.execute(
            select(func.coalesce(func.sum(ExtractedLiabilityModel.amount), 0.0))
            .where(ExtractedLiabilityModel.application_id == application_id)
        )
        features["total_liabilities"] = float(liabilities.scalar() or 0.0)

        annual_income = features["monthly_income"] * 12
        features["liability_to_income_ratio"] = (
            round(features["total_liabilities"] / (annual_income + 1), 4)
        )

        inc_count = await session.execute(
            select(func.count(InconsistencyModel.id))
            .where(InconsistencyModel.application_id == application_id)
        )
        features["has_inconsistencies"] = 1.0 if (inc_count.scalar() or 0) > 0 else 0.0

        doc_count = await session.execute(
            select(func.count(DocumentModel.id))
            .where(DocumentModel.application_id == application_id)
        )
        features["num_documents"] = float(doc_count.scalar() or 0)

        assessment = await session.execute(
            select(AssessmentModel.ml_score)
            .where(AssessmentModel.application_id == application_id)
            .limit(1)
        )
        assessment_row = assessment.first()
        label = None
        if assessment_row and assessment_row.ml_score is not None:
            label = 1.0 if assessment_row.ml_score >= 0.5 else 0.0

        return FeatureVector(
            application_id=application_id,
            features=features,
            label=label,
        )


async def extract_all_feature_vectors() -> list[FeatureVector]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(ApplicationModel.id)
        )
        app_ids = [row[0] for row in result.fetchall()]

    vectors = []
    for app_id in app_ids:
        fv = await extract_features_for_application(app_id)
        if fv is not None:
            vectors.append(fv)

    logger.info(f"Extracted {len(vectors)} feature vectors from {len(app_ids)} applications")
    return vectors
