from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class IncomeFrequency(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ONE_TIME = "one_time"
    WEEKLY = "weekly"


class IncomeSource(str, Enum):
    SALARY = "salary"
    BUSINESS = "business"
    RENTAL = "rental"
    INVESTMENT = "investment"
    GOVERNMENT_BENEFITS = "government_benefits"
    OTHER = "other"


@dataclass(frozen=True)
class Income:
    """Value object representing an income record.

    Frozen to ensure immutability — once created, income data cannot change.
    New income records should be created rather than modifying existing ones.
    """
    source: IncomeSource
    amount: Decimal
    currency: str = "AED"
    frequency: IncomeFrequency = IncomeFrequency.MONTHLY
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Income amount cannot be negative: {self.amount}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1: {self.confidence}")

    @property
    def monthly_amount(self) -> Decimal:
        """Normalize income to monthly amount for consistent comparison."""
        if self.frequency == IncomeFrequency.ANNUAL:
            return self.amount / Decimal("12")
        if self.frequency == IncomeFrequency.WEEKLY:
            return self.amount * Decimal("4.33")
        if self.frequency == IncomeFrequency.ONE_TIME:
            return Decimal("0")
        return self.amount

    @property
    def annual_amount(self) -> Decimal:
        """Normalize income to annual amount."""
        if self.frequency == IncomeFrequency.MONTHLY:
            return self.amount * Decimal("12")
        if self.frequency == IncomeFrequency.WEEKLY:
            return self.amount * Decimal("52")
        if self.frequency == IncomeFrequency.ONE_TIME:
            return self.amount
        return self.amount
