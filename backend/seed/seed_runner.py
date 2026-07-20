"""Database seeder that populates all 4 databases with synthetic data.

Usage:
    python -m backend.seed.seed_runner
"""

import asyncio
import random
from datetime import date, timedelta
from uuid import uuid4

from faker import Faker
from sqlalchemy import text
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
    async_session_factory,
    engine,
)
from backend.database.postgres.database import Base
from backend.database.mongodb.document_store import mongo_document_store
from backend.database.neo4j.graph_store import neo4j_graph_store
from backend.database.qdrant.vector_store import qdrant_vector_store
from backend.domain.entities.document import OCRStatus
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
                    relationship=fm["relationship"],
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
    logger.info("Seeding MongoDB...")
    await mongo_document_store.connect()
    for i in range(10):
        await mongo_document_store.save_ocr_result(
            application_id=uuid4(),
            document_id=uuid4(),
            text=f"Sample OCR text for document {i}: extracted bank statement showing salary credits of AED 4,200 monthly.",
            tables=[{"header": ["Date", "Description", "Amount"], "rows": [
                ["2024-01-01", "Salary Credit", "4200"],
                ["2024-01-05", "Rent Payment", "-2000"],
            ]}],
        )
    await mongo_document_store.close()
    logger.info("Seeded MongoDB with sample OCR results")


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
