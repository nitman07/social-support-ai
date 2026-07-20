from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from backend.domain.values.address import Address


@dataclass
class Applicant:
    """Aggregate root representing a social support applicant.

    Encapsulates all personal information and contact details.
    Serves as the primary entity for applicant-related operations.
    """
    full_name: str
    emirates_id: str
    date_of_birth: date
    nationality: str
    phone: str
    email: str
    address: Address
    id: UUID = field(default_factory=uuid4)
    passport_number: str | None = None

    def __post_init__(self) -> None:
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Full name is required")
        if not self.emirates_id or not self.emirates_id.strip():
            raise ValueError("Emirates ID is required")
        if not self.phone or not self.phone.strip():
            raise ValueError("Phone number is required")
        if not self.email or not self.email.strip():
            raise ValueError("Email is required")

    @property
    def age(self) -> int:
        """Calculate applicant's age from date of birth."""
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )
