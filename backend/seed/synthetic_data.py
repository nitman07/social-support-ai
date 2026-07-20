import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from faker import Faker

from backend.domain.entities.applicant import Applicant
from backend.domain.entities.application import Application
from backend.domain.entities.assessment import Assessment, Decision
from backend.domain.entities.document import Document, OCRStatus
from backend.domain.values.address import Address
from backend.domain.values.document_type import DocumentType
from backend.domain.values.eligibility_score import EligibilityScore
from backend.domain.values.income import Income, IncomeFrequency, IncomeSource

fake = Faker("en_US")


class SyntheticDataGenerator:
    """Generates realistic synthetic data for development and testing.

    Produces applicants with controlled distributions:
    - 60% low-income (eligible for support)
    - 25% middle-income (borderline eligibility)
    - 15% high-income or high-assets (likely ineligible)

    Includes optional inconsistencies for testing validation agent.
    """

    EMIRATES_ID_FORMAT = "784-{year}-{number}-{checksum}"

    def __init__(self, seed: int = 42) -> None:
        random.seed(seed)
        fake.seed_instance(seed)
        self._used_emirates_ids: set[str] = set()

    def generate_applicant(self) -> Applicant:
        """Generate a single realistic applicant with UAE-specific data."""
        gender = random.choice(["male", "female"])
        name = fake.name_male() if gender == "male" else fake.name_female()
        year = random.randint(1960, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dob = date(year, month, day)
        emirates_id = self._generate_emirates_id(year)

        applicant = Applicant(
            full_name=name,
            emirates_id=emirates_id,
            date_of_birth=dob,
            nationality=random.choice(["UAE", "Jordan", "Egypt", "Syria", "India", "Philippines", "Pakistan", "Bangladesh"]),
            phone=f"+971{random.randint(50, 58)}{random.randint(1000000, 9999999)}",
            email=fake.email(),
            address=Address(
                street=fake.street_address(),
                city=random.choice(["Abu Dhabi", "Dubai", "Sharjah", "Al Ain", "Ajman", "Ras Al Khaimah"]),
                emirate=random.choice(["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Ras Al Khaimah"]),
                po_box=str(random.randint(10000, 99999)),
            ),
        )
        return applicant

    def generate_application_with_assessment(
        self, applicant_id: UUID, include_inconsistencies: bool = False
    ) -> dict[str, Any]:
        """Generate a full application with all associated data."""
        app = Application(applicant_id=applicant_id)
        income_level = random.choices(
            ["low", "medium", "high"],
            weights=[0.60, 0.25, 0.15],
            k=1,
        )[0]

        income_data = self._generate_income(income_level)
        employment_data = self._generate_employment()
        family_data = self._generate_family()
        asset_data = self._generate_assets(income_level)
        liability_data = self._generate_liabilities(income_level)

        inconsistencies = []
        if include_inconsistencies:
            inconsistencies = self._generate_inconsistencies(income_data, employment_data)

        ml_score, confidence = self._compute_eligibility(
            income_data["monthly_income"],
            len(family_data),
            employment_data["years_employed"],
            asset_data["total_assets"],
            liability_data["total_liabilities"],
        )

        decision = self._determine_decision(ml_score)

        assessment = Assessment(application_id=app.id)
        if ml_score is not None:
            score = EligibilityScore(
                score=ml_score,
                confidence=confidence,
                feature_importance={
                    "monthly_income": 0.32,
                    "family_size": 0.28,
                    "employment_years": 0.15,
                    "liability_to_income_ratio": 0.12,
                    "credit_score": 0.08,
                    "total_assets": 0.05,
                },
            )
            assessment.record_ml_result(score)

        if decision == "approved":
            assessment.approve(decided_by="system")
        elif decision == "soft_decline":
            assessment.soft_decline(decided_by="system")

        return {
            "application": app,
            "income": income_data,
            "employment": employment_data,
            "family": family_data,
            "assets": asset_data,
            "liabilities": liability_data,
            "inconsistencies": inconsistencies,
            "assessment": assessment,
            "ml_score": ml_score,
            "confidence": confidence,
            "decision": decision,
        }

    def generate_document(self, application_id: UUID, doc_type: DocumentType) -> Document:
        return Document(
            application_id=application_id,
            document_type=doc_type,
            file_name=f"{doc_type.value}_{uuid4().hex[:8]}.pdf",
            mime_type="application/pdf",
            file_size=random.randint(50000, 2000000),
            storage_path=f"applications/{application_id}/{doc_type.value}.pdf",
            ocr_status=OCRStatus.COMPLETED,
            ocr_confidence=random.uniform(0.75, 0.99),
        )

    def generate_policy_document(self, policy_id: str, title: str, category: str) -> dict:
        return {
            "id": policy_id,
            "title": title,
            "category": category,
            "content": self._generate_policy_content(title, category),
            "effective_from": str(date.today() - timedelta(days=random.randint(1, 365))),
            "effective_to": str(date.today() + timedelta(days=random.randint(365, 1095))),
        }

    def _generate_emirates_id(self, birth_year: int) -> str:
        while True:
            num = random.randint(1000000, 9999999)
            checksum = random.randint(0, 9)
            eid = self.EMIRATES_ID_FORMAT.format(year=birth_year, number=num, checksum=checksum)
            if eid not in self._used_emirates_ids:
                self._used_emirates_ids.add(eid)
                return eid

    def _generate_income(self, level: str) -> dict:
        if level == "low":
            monthly = round(random.uniform(1500, 5000), 2)
        elif level == "medium":
            monthly = round(random.uniform(5000, 15000), 2)
        else:
            monthly = round(random.uniform(15000, 50000), 2)

        return {
            "monthly_income": monthly,
            "source": random.choice(["salary", "business", "rental", "government_benefits"]),
            "currency": "AED",
            "frequency": "monthly",
        }

    def _generate_employment(self) -> dict:
        years = round(random.uniform(0, 20), 1)
        return {
            "employer_name": fake.company(),
            "position": fake.job(),
            "years_employed": years,
            "start_date": str(date.today() - timedelta(days=int(years * 365))),
            "is_current": random.random() > 0.2,
        }

    def _generate_family(self) -> list[dict]:
        size = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[0.1, 0.15, 0.25, 0.25, 0.15, 0.05, 0.05], k=1)[0]
        members = []
        for i in range(size):
            is_spouse = i == 0
            members.append({
                "name": fake.name(),
                "relationship": "spouse" if is_spouse else "child",
                "is_dependent": not is_spouse,
            })
        return members

    def _generate_assets(self, income_level: str) -> dict:
        if income_level == "high":
            total = round(random.uniform(200000, 2000000), 2)
        elif income_level == "medium":
            total = round(random.uniform(20000, 200000), 2)
        else:
            total = round(random.uniform(0, 30000), 2)
        return {
            "total_assets": total,
            "items": [
                {"type": "vehicle", "value": round(total * random.uniform(0.3, 0.6), 2)},
                {"type": "bank_account", "value": round(total * random.uniform(0.1, 0.3), 2)},
            ],
        }

    def _generate_liabilities(self, income_level: str) -> dict:
        if income_level == "high":
            total = round(random.uniform(50000, 500000), 2)
        elif income_level == "medium":
            total = round(random.uniform(5000, 100000), 2)
        else:
            total = round(random.uniform(0, 15000), 2)
        monthly_payment = round(total * random.uniform(0.02, 0.05), 2)
        return {
            "total_liabilities": total,
            "monthly_payment": monthly_payment,
            "items": [
                {"type": random.choice(["loan", "credit_card", "mortgage"]), "amount": total},
            ],
        }

    def _generate_inconsistencies(self, income: dict, employment: dict) -> list[dict]:
        inconsistencies = []
        if random.random() < 0.3:
            inconsistencies.append({
                "field": "income_amount",
                "source_a": "salary_certificate",
                "value_a": str(income["monthly_income"]),
                "source_b": "bank_statement",
                "value_b": str(round(income["monthly_income"] * random.uniform(0.8, 0.95), 2)),
                "severity": "medium",
            })
        if random.random() < 0.2:
            inconsistencies.append({
                "field": "employer_name",
                "source_a": "resume",
                "value_a": employment["employer_name"],
                "source_b": "salary_certificate",
                "value_b": fake.company(),
                "severity": "high",
            })
        return inconsistencies

    def _compute_eligibility(
        self,
        monthly_income: float,
        family_size: int,
        years_employed: float,
        total_assets: float,
        total_liabilities: float,
    ) -> tuple[float, float]:
        score = 0.5

        if monthly_income < 3000:
            score += 0.3
        elif monthly_income < 5000:
            score += 0.2
        elif monthly_income > 20000:
            score -= 0.3

        if family_size >= 4:
            score += 0.2
        elif family_size >= 2:
            score += 0.1

        if years_employed >= 2:
            score += 0.15
        elif years_employed >= 1:
            score += 0.05
        else:
            score -= 0.1

        if total_assets > 500000:
            score -= 0.3
        elif total_assets > 200000:
            score -= 0.15

        liability_ratio = total_liabilities / (monthly_income * 12 + 1)
        if liability_ratio > 2:
            score -= 0.2
        elif liability_ratio > 1:
            score -= 0.1

        score = max(0.0, min(1.0, score))
        confidence = random.uniform(0.75, 0.95)

        return round(score, 2), round(confidence, 2)

    def _determine_decision(self, score: float) -> str:
        if score >= 0.55:
            return "approved"
        elif score >= 0.35:
            return "soft_decline"
        return "declined"

    def _generate_policy_content(self, title: str, category: str) -> str:
        return f"""
{title}

Category: {category}
Effective Date: Recent
Applicable To: UAE nationals and residents

Eligibility Criteria:
1. Monthly household income must be below AED 5,000 for single applicants
2. Monthly household income must be below AED 8,000 for families with dependents
3. Total assets excluding primary residence must not exceed AED 500,000
4. Applicant must have valid Emirates ID and residence visa
5. Family size is calculated including spouse and dependent children under 21

Support Amounts:
- Single applicant: AED 2,000 - 3,000 per month
- Family of 2: AED 3,000 - 4,500 per month
- Family of 3-4: AED 3,500 - 5,000 per month
- Family of 5+: AED 4,000 - 6,000 per month

Additional Benefits:
- Healthcare coverage for approved applicants
- Educational support for dependent children
- Vocational training programs (mandatory for able-bodied applicants under 40)
- Job placement assistance through partner employers

Review Period:
- Initial approval valid for 12 months
- Renewal requires updated income and employment verification
- Random audits conducted on 5% of approved cases
"""


generator = SyntheticDataGenerator()
