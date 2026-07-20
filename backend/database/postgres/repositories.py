from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ApplicationNotFoundError, ApplicantNotFoundError
from backend.domain.entities.applicant import Applicant
from backend.domain.entities.application import Application, ApplicationStatus
from backend.domain.entities.document import Document, OCRStatus
from backend.domain.entities.assessment import Assessment, Decision
from backend.domain.ports import IApplicantRepository, IApplicationRepository
from backend.domain.values.address import Address
from backend.database.postgres.models import (
    ApplicantModel,
    ApplicationModel,
    AssessmentModel,
    DocumentModel,
)


class PostgresApplicantRepository(IApplicantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, applicant: Applicant) -> Applicant:
        model = ApplicantModel(
            id=applicant.id,
            full_name=applicant.full_name,
            emirates_id=applicant.emirates_id,
            passport_number=applicant.passport_number,
            date_of_birth=applicant.date_of_birth,
            nationality=applicant.nationality,
            phone=applicant.phone,
            email=applicant.email,
            address={
                "street": applicant.address.street,
                "city": applicant.address.city,
                "emirate": applicant.address.emirate,
                "po_box": applicant.address.po_box,
                "country": applicant.address.country,
            },
        )
        self.session.add(model)
        await self.session.flush()
        return applicant

    async def get_by_id(self, applicant_id: UUID) -> Applicant | None:
        result = await self.session.execute(
            select(ApplicantModel).where(ApplicantModel.id == applicant_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_emirates_id(self, emirates_id: str) -> Applicant | None:
        result = await self.session.execute(
            select(ApplicantModel).where(ApplicantModel.emirates_id == emirates_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, applicant: Applicant) -> Applicant:
        result = await self.session.execute(
            select(ApplicantModel).where(ApplicantModel.id == applicant.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ApplicantNotFoundError(str(applicant.id))
        model.full_name = applicant.full_name
        model.phone = applicant.phone
        model.email = applicant.email
        model.address = {
            "street": applicant.address.street,
            "city": applicant.address.city,
            "emirate": applicant.address.emirate,
            "po_box": applicant.address.po_box,
            "country": applicant.address.country,
        }
        await self.session.flush()
        return applicant

    def _to_domain(self, model: ApplicantModel) -> Applicant:
        return Applicant(
            id=model.id,
            full_name=model.full_name,
            emirates_id=model.emirates_id,
            passport_number=model.passport_number,
            date_of_birth=model.date_of_birth,
            nationality=model.nationality,
            phone=model.phone,
            email=model.email,
            address=Address(
                street=model.address["street"],
                city=model.address["city"],
                emirate=model.address["emirate"],
                po_box=model.address.get("po_box"),
                country=model.address.get("country", "UAE"),
            ),
        )


class PostgresApplicationRepository(IApplicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, application: Application) -> Application:
        model = ApplicationModel(
            id=application.id,
            applicant_id=application.applicant_id,
            status=application.status.value,
            app_metadata=application.metadata,
        )
        self.session.add(model)
        await self.session.flush()
        return application

    async def get_by_id(self, application_id: UUID) -> Application | None:
        result = await self.session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_applicant_id(self, applicant_id: UUID) -> list[Application]:
        result = await self.session.execute(
            select(ApplicationModel)
            .where(ApplicationModel.applicant_id == applicant_id)
            .order_by(ApplicationModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, application: Application) -> Application:
        result = await self.session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ApplicationNotFoundError(str(application.id))
        model.status = application.status.value
        model.workflow_id = application.workflow_id
        model.checkpoint_id = application.checkpoint_id
        model.app_metadata = application.metadata
        model.submitted_at = application.submitted_at
        model.completed_at = application.completed_at
        await self.session.flush()
        return application

    async def update_status(self, application_id: UUID, status: ApplicationStatus) -> None:
        result = await self.session.execute(
            select(ApplicationModel).where(ApplicationModel.id == application_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ApplicationNotFoundError(str(application_id))
        model.status = status.value
        await self.session.flush()

    async def list_by_status(
        self, status: ApplicationStatus, limit: int = 20, offset: int = 0
    ) -> list[Application]:
        result = await self.session.execute(
            select(ApplicationModel)
            .where(ApplicationModel.status == status.value)
            .order_by(ApplicationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_status(self, status: ApplicationStatus | None = None) -> int:
        query = select(func.count(ApplicationModel.id))
        if status:
            query = query.where(ApplicationModel.status == status.value)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, application_id: UUID) -> None:
        await self.session.execute(
            delete(ApplicationModel).where(ApplicationModel.id == application_id)
        )
        await self.session.flush()

    def _to_domain(self, model: ApplicationModel) -> Application:
        return Application(
            id=model.id,
            applicant_id=model.applicant_id,
            status=ApplicationStatus(model.status),
            workflow_id=model.workflow_id,
            checkpoint_id=model.checkpoint_id,
            metadata=model.app_metadata,
            submitted_at=model.submitted_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )
