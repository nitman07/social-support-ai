from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from backend.domain.values.document_type import DocumentType


class OCRStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:
    """Entity representing an uploaded application document.

    Tracks the document's processing state through the OCR pipeline.
    Each document belongs to a single application and has a specific type
    that determines how it should be processed.
    """
    application_id: UUID
    document_type: DocumentType
    file_name: str
    mime_type: str
    file_size: int
    storage_path: str
    id: UUID = field(default_factory=uuid4)
    ocr_status: OCRStatus = OCRStatus.PENDING
    ocr_confidence: float | None = None
    extracted_text: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.file_size <= 0:
            raise ValueError(f"File size must be positive: {self.file_size}")
        if self.ocr_confidence is not None and not 0 <= self.ocr_confidence <= 1:
            raise ValueError(f"OCR confidence must be between 0 and 1: {self.ocr_confidence}")

    def mark_processing(self) -> None:
        self.ocr_status = OCRStatus.PROCESSING

    def mark_completed(self, confidence: float, extracted_text: str) -> None:
        self.ocr_status = OCRStatus.COMPLETED
        self.ocr_confidence = confidence
        self.extracted_text = extracted_text

    def mark_failed(self) -> None:
        self.ocr_status = OCRStatus.FAILED
        self.retry_count += 1

    @property
    def is_processable(self) -> bool:
        return self.ocr_status in {OCRStatus.PENDING, OCRStatus.FAILED}

    @property
    def file_extension(self) -> str:
        return self.file_name.rsplit(".", 1)[-1].lower() if "." in self.file_name else ""
