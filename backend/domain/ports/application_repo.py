from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from backend.domain.entities.application import Application, ApplicationStatus

if TYPE_CHECKING:
    from backend.domain.entities.applicant import Applicant


class IApplicationRepository(ABC):
    """Interface for application persistence.

    Implementations can use PostgreSQL, in-memory storage, or any
    other storage backend without affecting domain logic.
    """

    @abstractmethod
    async def create(self, application: Application) -> Application:
        ...

    @abstractmethod
    async def get_by_id(self, application_id: UUID) -> Application | None:
        ...

    @abstractmethod
    async def get_by_applicant_id(self, applicant_id: UUID) -> list[Application]:
        ...

    @abstractmethod
    async def update(self, application: Application) -> Application:
        ...

    @abstractmethod
    async def update_status(self, application_id: UUID, status: ApplicationStatus) -> None:
        ...

    @abstractmethod
    async def list_by_status(
        self, status: ApplicationStatus, limit: int = 20, offset: int = 0
    ) -> list[Application]:
        ...

    @abstractmethod
    async def count_by_status(self, status: ApplicationStatus | None = None) -> int:
        ...

    @abstractmethod
    async def delete(self, application_id: UUID) -> None:
        ...


class IApplicantRepository(ABC):
    """Interface for applicant persistence."""

    @abstractmethod
    async def create(self, applicant: Applicant) -> Applicant:
        ...

    @abstractmethod
    async def get_by_id(self, applicant_id: UUID) -> Applicant | None:
        ...

    @abstractmethod
    async def get_by_emirates_id(self, emirates_id: str) -> Applicant | None:
        ...

    @abstractmethod
    async def update(self, applicant: Applicant) -> Applicant:
        ...
