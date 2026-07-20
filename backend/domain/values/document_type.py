from enum import Enum


class DocumentType(str, Enum):
    """Supported document types for social support applications."""

    EMIRATES_ID = "emirates_id"
    PASSPORT = "passport"
    RESUME = "resume"
    CREDIT_REPORT = "credit_report"
    BANK_STATEMENT = "bank_statement"
    SALARY_CERTIFICATE = "salary_certificate"
    ASSETS_LIABILITIES = "assets_liabilities"
    FAMILY_DOCUMENT = "family_document"
    INCOME_PROOF = "income_proof"
    OTHER = "other"

    @classmethod
    def requires_ocr(cls, doc_type: str) -> bool:
        """Check if a document type typically requires OCR processing."""
        return doc_type in {
            cls.EMIRATES_ID,
            cls.PASSPORT,
            cls.FAMILY_DOCUMENT,
            cls.INCOME_PROOF,
        }

    @classmethod
    def requires_table_extraction(cls, doc_type: str) -> bool:
        """Check if a document type contains tabular data."""
        return doc_type in {
            cls.BANK_STATEMENT,
            cls.ASSETS_LIABILITIES,
            cls.CREDIT_REPORT,
        }

    @property
    def display_name(self) -> str:
        return {
            "emirates_id": "Emirates ID",
            "passport": "Passport",
            "resume": "Resume/CV",
            "credit_report": "Credit Report",
            "bank_statement": "Bank Statement",
            "salary_certificate": "Salary Certificate",
            "assets_liabilities": "Assets & Liabilities",
            "family_document": "Family Document",
            "income_proof": "Income Proof",
            "other": "Other Document",
        }[self.value]
