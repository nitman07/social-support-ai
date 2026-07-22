"""Database seeder that populates all 4 databases with synthetic data.

Usage:
    python -m backend.seed.seed_runner
"""

import asyncio
import io
import random
from datetime import date, timedelta
from uuid import UUID, uuid4

from faker import Faker
from fpdf import FPDF
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.postgres import (
    ApplicantModel,
    ApplicationModel,
    AssessmentModel,
    DocumentModel,
    ExtractedIncomeModel,
    ExtractedEmploymentModel,
    FamilyMemberModel,
    ExtractedAssetModel,
    ExtractedLiabilityModel,
    InconsistencyModel,
    RecommendationModel,
    UserModel,
    async_session_factory,
    engine,
)
from backend.services.auth_service import hash_password
from backend.database.postgres.database import Base
from backend.database.mongodb.document_store import mongo_document_store
from backend.database.neo4j.graph_store import neo4j_graph_store
from backend.database.qdrant.vector_store import qdrant_vector_store
from backend.domain.entities.document import Document, DocumentType, OCRStatus
from backend.domain.ports import VectorRecord
from backend.seed.synthetic_data import generator

logger = get_logger(__name__)
fake = Faker()

NUM_APPLICANTS = 100
EMBEDDING_SIZE = 768


async def seed_postgres() -> None:
    logger.info("Seeding PostgreSQL...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        session.add_all([
            UserModel(
                id=uuid4(),
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
                full_name="System Administrator",
                active=True,
            ),
            UserModel(
                id=uuid4(),
                username="reviewer",
                hashed_password=hash_password("reviewer123"),
                role="reviewer",
                full_name="Senior Reviewer",
                active=True,
            ),
        ])
        await session.flush()

        for i in range(NUM_APPLICANTS):
            applicant = generator.generate_applicant()
            include_inconsistencies = i % 3 == 0
            app_data = generator.generate_application_with_assessment(
                applicant.id, include_inconsistencies=include_inconsistencies
            )
            app = app_data["application"]
            assessment = app_data["assessment"]

            session.add(ApplicantModel(
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
            ))

            session.add(ApplicationModel(
                id=app.id,
                applicant_id=applicant.id,
                status=app.status.value,
            ))

            for doc_type_name in random.sample(
                ["emirates_id", "passport", "bank_statement", "salary_certificate", "resume", "assets_liabilities"],
                k=random.randint(3, 5),
            ):
                doc_id = uuid4()
                session.add(DocumentModel(
                    id=doc_id,
                    application_id=app.id,
                    document_type=doc_type_name,
                    file_name=f"{doc_type_name}_{doc_id.hex[:8]}.pdf",
                    mime_type="application/pdf",
                    file_size=random.randint(50000, 2000000),
                    storage_path=f"applications/{app.id}/{doc_type_name}.pdf",
                    ocr_status=OCRStatus.COMPLETED.value,
                    ocr_confidence=round(random.uniform(0.75, 0.99), 2),
                ))

            income = app_data["income"]
            session.add(ExtractedIncomeModel(
                id=uuid4(),
                application_id=app.id,
                source=income["source"],
                amount=income["monthly_income"],
                currency=income.get("currency", "AED"),
                frequency=income.get("frequency", "monthly"),
            ))

            emp = app_data["employment"]
            session.add(ExtractedEmploymentModel(
                id=uuid4(),
                application_id=app.id,
                employer_name=emp["employer_name"],
                position=emp.get("position", "Employee"),
                start_date=date.today() - timedelta(days=int(emp["years_employed"] * 365)),
                is_current=emp["is_current"],
                confidence=0.95,
            ))

            for fm in app_data["family"]:
                session.add(FamilyMemberModel(
                    id=uuid4(),
                    application_id=app.id,
                    name=fm["name"],
                    relation=fm["relationship"],
                    is_dependent=fm["is_dependent"],
                ))

            session.add(ExtractedAssetModel(
                id=uuid4(),
                application_id=app.id,
                asset_type="total",
                value=app_data["assets"]["total_assets"],
            ))

            session.add(ExtractedLiabilityModel(
                id=uuid4(),
                application_id=app.id,
                liability_type="total",
                amount=app_data["liabilities"]["total_liabilities"],
                monthly_payment=app_data["liabilities"]["monthly_payment"],
            ))

            for inc in app_data["inconsistencies"]:
                session.add(InconsistencyModel(
                    id=uuid4(),
                    application_id=app.id,
                    field=inc["field"],
                    source_a=inc["source_a"],
                    value_a=inc["value_a"],
                    source_b=inc["source_b"],
                    value_b=inc["value_b"],
                    severity=inc["severity"],
                ))

            assessment_model = AssessmentModel(
                id=uuid4(),
                application_id=app.id,
                ml_score=app_data["ml_score"],
                ml_confidence=app_data["confidence"],
                decision=app_data["decision"],
                decided_by="system",
            )
            session.add(assessment_model)
            await session.flush()

            session.add(RecommendationModel(
                id=uuid4(),
                assessment_id=assessment_model.id,
                category="training",
                title="UAE Digital Skills Program",
                description="Free 6-month online program covering digital literacy and basic coding",
                relevance_score=0.85,
            ))

        await session.commit()

    logger.info(f"Seeded {NUM_APPLICANTS} applicants into PostgreSQL")


async def seed_mongodb() -> None:
    logger.info("Seeding MongoDB with documents and OCR results...")
    await mongo_document_store.connect()

    async with async_session_factory() as session:
        result = await session.execute(select(DocumentModel))
        all_docs = result.scalars().all()

    for doc_model in all_docs:
        pdf_bytes = _generate_dummy_pdf(doc_model.document_type, doc_model.file_name)
        doc_entity = Document(
            application_id=doc_model.application_id,
            document_type=DocumentType(doc_model.document_type),
            file_name=doc_model.file_name,
            mime_type=doc_model.mime_type,
            file_size=len(pdf_bytes),
            storage_path=doc_model.storage_path,
            id=doc_model.id,
            ocr_status=OCRStatus(doc_model.ocr_status),
            ocr_confidence=doc_model.ocr_confidence,
        )
        await mongo_document_store.upload(doc_entity, pdf_bytes)

        await mongo_document_store.save_ocr_result(
            application_id=doc_model.application_id,
            document_id=doc_model.id,
            text=f"Extracted text from {doc_model.document_type}: sample data for verification purposes.",
            tables=[{"header": ["Field", "Value"], "rows": [
                ["document_type", doc_model.document_type],
                ["ocr_confidence", str(doc_model.ocr_confidence)],
            ]}],
        )

    await mongo_document_store.close()
    logger.info(f"Seeded {len(all_docs)} documents into MongoDB GridFS")


def _generate_dummy_pdf(doc_type: str, file_name: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, text=f"Document: {doc_type}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, text=f"File: {file_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.multi_cell(0, 8, text=f"This is a sample {doc_type.replace('_', ' ').title()} document generated for testing purposes. It contains dummy data for the Social Support AI workflow automation system.")
    pdf.ln(10)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 8, text="Extracted Data:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    sample_data = {
        "emirates_id": "784-1992-1234567-1\nName: John Doe\nNationality: UAE\nDate of Birth: 15/03/1992",
        "passport": "Passport No: P12345678\nFull Name: John Doe\nNationality: UAE\nIssue Date: 01/01/2020\nExpiry: 31/12/2030",
        "bank_statement": "Bank: UAE National Bank\nAccount: AE123456789012345678901\nPeriod: Jan-Dec 2024\nTotal Credits: AED 48,000\nTotal Debits: AED 36,000",
        "salary_certificate": "Employer: ABC Company LLC\nEmployee: John Doe\nMonthly Salary: AED 4,200\nPosition: Administrative Assistant\nDate: 01/01/2024",
        "resume": "Name: John Doe\nExperience: 5 years\nSkills: Microsoft Office, Data Entry\nEducation: Bachelor's Degree",
        "assets_liabilities": "Assets:\n- Vehicle: AED 45,000\n- Bank Account: AED 12,500\nLiabilities:\n- Personal Loan: AED 15,000\nMonthly Payment: AED 500",
    }
    pdf.multi_cell(0, 8, text=sample_data.get(doc_type, f"Sample data for {doc_type}"))
    return pdf.output()


async def seed_qdrant() -> None:
    logger.info("Seeding Qdrant...")

    for collection in [
        qdrant_vector_store.COLLECTION_POLICIES,
        qdrant_vector_store.COLLECTION_PROGRAMS,
        qdrant_vector_store.COLLECTION_FAQS,
    ]:
        await qdrant_vector_store.create_collection(collection, EMBEDDING_SIZE)

    policies = []
    for i in range(20):
        policy = generator.generate_policy_document(
            policy_id=f"policy_{i}",
            title=f"Social Support Policy - Category {i % 5}",
            category=random.choice(["eligibility", "support_amount", "special_programs"]),
        )
        policies.append(policy)

    policy_records = [
        VectorRecord(
            id=p["id"],
            vector=[random.uniform(-1, 1) for _ in range(EMBEDDING_SIZE)],
            payload={
                "title": p["title"],
                "category": p["category"],
                "effective_from": p["effective_from"],
                "effective_to": p["effective_to"],
            },
        )
        for p in policies
    ]
    await qdrant_vector_store.upsert(qdrant_vector_store.COLLECTION_POLICIES, policy_records)
    logger.info(f"Seeded {len(policies)} policy documents into Qdrant")


async def seed_neo4j() -> None:
    logger.info("Seeding Neo4j...")

    await neo4j_graph_store.connect()
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id, full_name, nationality FROM applicants LIMIT 20")
        )
        applicants = result.fetchall()

        for row in applicants:
            await neo4j_graph_store.build_applicant_graph(
                applicant_id=row[0],
                family_members=[
                    {"name": f"Spouse of {row[1]}", "relationship": "spouse", "is_dependent": False},
                    {"name": f"Child of {row[1]}", "relationship": "child", "is_dependent": True},
                ],
                employers=[{"name": fake.company(), "position": "Employee", "start_date": "2020-01-01"}],
                assets=[{"type": "vehicle", "value": 45000, "description": "Car"}],
                liabilities=[{"type": "loan", "amount": 15000, "monthly_payment": 500}],
            )

    await neo4j_graph_store.close()
    logger.info("Seeded Neo4j with applicant graphs")


async def main() -> None:
    logger.info("Starting database seeding...")
    await seed_postgres()
    await seed_mongodb()
    await seed_qdrant()
    await seed_neo4j()
    logger.info("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
