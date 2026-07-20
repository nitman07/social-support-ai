from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """Value object representing a UAE address.

    Immutable by design. Address changes create new instances.
    """
    street: str
    city: str
    emirate: str
    po_box: str | None = None
    country: str = "UAE"

    def __post_init__(self) -> None:
        if not self.street or not self.street.strip():
            raise ValueError("Street address is required")
        if not self.city or not self.city.strip():
            raise ValueError("City is required")
        if not self.emirate or not self.emirate.strip():
            raise ValueError("Emirate is required")

    @property
    def full_address(self) -> str:
        parts = [self.street, self.city, self.emirate, self.country]
        if self.po_box:
            parts.insert(3, f"PO Box {self.po_box}")
        return ", ".join(parts)

    def matches(self, other: "Address") -> bool:
        """Check if two addresses refer to the same location (fuzzy match)."""
        return (
            self.street.lower().strip() == other.street.lower().strip()
            and self.city.lower().strip() == other.city.lower().strip()
            and self.emirate.lower().strip() == other.emirate.lower().strip()
        )
