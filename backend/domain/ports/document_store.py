from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from backend.domain.entities.document import Document


class IDocumentStore(ABC):
    """Interface for document storage and retrieval.

    Implementations can use MongoDB GridFS, local filesystem, or
    cloud object storage without affecting domain logic.
    """

    @abstractmethod
    async def upload(self, document: Document, content: bytes) -> str:
        """Store document binary content and return storage path."""
        ...

    @abstractmethod
    async def download(self, document: Document) -> bytes:
        """Retrieve document binary content by storage path."""
        ...

    @abstractmethod
    async def delete(self, document: Document) -> None:
        """Remove document content from storage."""
        ...

    @abstractmethod
    async def save_ocr_result(
        self, application_id: UUID, document_id: UUID, text: str, tables: list[dict] | None = None
    ) -> None:
        """Store OCR extraction results for audit and reprocessing."""
        ...

    @abstractmethod
    async def get_ocr_result(self, application_id: UUID, document_id: UUID) -> dict | None:
        """Retrieve previously stored OCR results."""
        ...
