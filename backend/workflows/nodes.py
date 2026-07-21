import json
from uuid import uuid4

from backend.core.logging import get_logger
from backend.core.observability import trace_node
from backend.database.mongodb.document_store import mongo_document_store
from backend.database.neo4j.graph_store import neo4j_graph_store
from backend.database.postgres import (
    ApplicationModel,
    AssessmentModel,
    DocumentModel,
    ExtractedAssetModel,
    ExtractedEmploymentModel,
    ExtractedIncomeModel,
    ExtractedLiabilityModel,
    FamilyMemberModel,
    InconsistencyModel,
    RecommendationModel,
    async_session_factory,
)
from backend.database.qdrant.vector_store import qdrant_vector_store
from backend.ml.features import extract_features_for_application
from backend.ml.model import ml_service
from backend.ml.rules import evaluate_all_rules
from backend.rag.retriever import retrieve_policies
from backend.services.llm_service import llm_service
from backend.workflows.state import ApplicationState, DocumentInfo, Inconsistency, PolicyContext, Recommendation, RuleResult
from sqlalchemy import select, text

logger = get_logger(__name__)


@trace_node("intake")
async def intake_node(state: ApplicationState) -> dict:
    application_id = state["application_id"]
    logger.info(f"Intake: processing application {application_id}")

    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if app is None:
            return {"errors": state["errors"] + [f"Application {application_id} not found"]}

        app.status = "processing"
        session.add(app)
        await session.commit()

    async with async_session_factory() as session:
        result = await session.execute(
            select(DocumentModel)
            .where(DocumentModel.application_id == application_id)
        )
        documents = []
        for row in result.scalars():
            documents.append(DocumentInfo(
                id=str(row.id),
                document_type=row.document_type,
                file_name=row.file_name,
                ocr_status=row.ocr_status,
                ocr_confidence=row.ocr_confidence or 0.0,
            ))

    return {
        "status": "processing",
        "documents": documents,
        "extraction_complete": False,
        "validation_complete": False,
    }


@trace_node("ocr")
async def ocr_node(state: ApplicationState) -> dict:
    logger.info(f"OCR: processing documents for application {state['application_id']}")
    ocr_results = {}

    for doc in state["documents"]:
        if doc["ocr_status"] == "completed":
            ocr_results[doc["document_type"]] = {
                "text": f"Sample OCR text for {doc['document_type']}",
                "confidence": doc["ocr_confidence"],
            }
            continue
        try:
            sample_text = f"Extracted text from {doc['file_name']}: applicant data and financial information."
            await mongo_document_store.save_ocr_result(
                application_id=state["application_id"],
                document_id=doc["id"],
                text=sample_text,
                tables=[{"header": ["Field", "Value"], "rows": [["sample", "data"]]}],
            )
            ocr_results[doc["document_type"]] = {
                "text": sample_text,
                "confidence": 0.85,
            }
        except Exception as e:
            logger.error(f"OCR failed for document {doc['id']}: {e}")

    return {
        "ocr_results": ocr_results,
        "extraction_complete": len(ocr_results) > 0,
    }


@trace_node("validation")
async def validation_node(state: ApplicationState) -> dict:
    logger.info(f"Validation: checking application {state['application_id']}")
    async with async_session_factory() as session:
        result = await session.execute(
            select(InconsistencyModel)
            .where(InconsistencyModel.application_id == state["application_id"])
        )
        inconsistencies = []
        for row in result.scalars():
            inconsistencies.append(Inconsistency(
                field=row.field,
                source_a=row.source_a,
                value_a=row.value_a,
                source_b=row.source_b,
                value_b=row.value_b,
                severity=row.severity,
            ))

    requires_review = len([i for i in inconsistencies if i["severity"] == "high"]) > 0
    return {
        "inconsistencies": inconsistencies,
        "validation_complete": True,
        "requires_human_review": requires_review,
    }


@trace_node("human_review")
async def human_review_node(state: ApplicationState) -> dict:
    logger.info(f"Human review: application {state['application_id']} flagged")
    return {
        "status": "awaiting_review",
    }


@trace_node("knowledge")
async def knowledge_node(state: ApplicationState) -> dict:
    logger.info(f"Knowledge: retrieving policies for application {state['application_id']}")
    policies = await retrieve_policies(
        "What are the current social support eligibility criteria and programs?"
    )
    return {
        "retrieved_policies": policies,
    }


@trace_node("eligibility")
async def eligibility_node(state: ApplicationState) -> dict:
    logger.info(f"Eligibility: computing score for application {state['application_id']}")
    fv = await extract_features_for_application(state["application_id"])
    if fv is None:
        return {"errors": state["errors"] + ["Feature extraction returned None"]}

    features = fv.features
    rules = await ml_service.evaluate_rules(features)

    rule_results = []
    for r in rules:
        rule_results.append(RuleResult(
            rule_name=r.rule_name,
            passed=r.passed,
            details=r.details,
        ))

    hard_blocked = any(
        not r.passed and r.rule_name in ("income_too_high", "asset_threshold", "debt_burden", "minimum_income")
        for r in rules
    )
    if hard_blocked:
        logger.info(f"Application {state['application_id']} blocked by hard rules")
        return {
            "ml_features": features,
            "ml_score": 0.0,
            "ml_confidence": 1.0,
            "ml_feature_importance": {},
            "eligibility_rules_applied": rule_results,
            "decision": "declined",
            "decision_rationale": "Application blocked by eligibility rules",
            "decision_confidence": 1.0,
        }

    if await ml_service.is_model_loaded():
        pred = await ml_service.predict(features)
        return {
            "ml_features": features,
            "ml_score": pred.score,
            "ml_confidence": pred.confidence,
            "ml_feature_importance": pred.feature_importance,
            "eligibility_rules_applied": rule_results,
        }

    return {
        "ml_features": features,
        "ml_score": None,
        "ml_confidence": None,
        "ml_feature_importance": {},
        "eligibility_rules_applied": rule_results,
    }


@trace_node("decision")
async def decision_node(state: ApplicationState) -> dict:
    logger.info(f"Decision: generating rationale for application {state['application_id']}")

    ml_score = state.get("ml_score")
    if ml_score is None:
        return {
            "decision": "pending",
            "decision_rationale": "ML model not available, requiring human review",
            "decision_confidence": 0.0,
        }

    if ml_score >= 0.55:
        decision = "approved"
    elif ml_score >= 0.4:
        decision = "referred"
    else:
        decision = "declined"

    top_features = sorted(
        state.get("ml_feature_importance", {}).items(),
        key=lambda x: -abs(x[1]),
    )[:3]
    feature_str = ", ".join(f"{name}: {val:.3f}" for name, val in top_features)

    policies = state.get("retrieved_policies", [])
    policy_str = "\n".join(
        f"- {p['title']} (score: {p['relevance_score']:.2f})"
        for p in policies[:2]
    )

    prompt = (
        f"Application {state['application_id']} has ML score {ml_score:.4f} "
        f"with confidence {state.get('ml_confidence', 0):.4f}.\n"
        f"Top contributing features: {feature_str}\n"
        f"Relevant policies:\n{policy_str}\n\n"
        f"Based on this data, the system recommends: {decision}.\n"
        f"Provide a brief, clear rationale for this decision in plain language."
    )

    try:
        response = await llm_service.generate(prompt=prompt)
        rationale = response.content
    except Exception as e:
        rationale = f"Decision based on ML score of {ml_score:.2f}. Top factors: {feature_str}"

    confidence = abs(ml_score - 0.5) * 2 if ml_score else 0.0

    return {
        "decision": decision,
        "decision_rationale": rationale,
        "decision_confidence": round(min(confidence + 0.3, 1.0), 4),
    }


@trace_node("recommendation")
async def recommendation_node(state: ApplicationState) -> dict:
    logger.info(f"Recommendation: generating for application {state['application_id']}")

    recs = [
        Recommendation(
            category="training",
            title="UAE Digital Skills Program",
            description="Free 6-month online program covering digital literacy and basic coding",
            relevance_score=0.85,
        ),
        Recommendation(
            category="employment",
            title="Job Placement Assistance",
            description="Government-sponsored job matching and career counseling services",
            relevance_score=0.75,
        ),
        Recommendation(
            category="support",
            title="Financial Counseling",
            description="Free financial planning and debt management advisory services",
            relevance_score=0.70,
        ),
    ]

    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, state["application_id"])
        if app:
            app.status = state.get("decision", "pending") if state.get("decision") != "referred" else "pending"
            session.add(app)

            assessment_result = await session.execute(
                select(AssessmentModel)
                .where(AssessmentModel.application_id == state["application_id"])
                .limit(1)
            )
            assessment = assessment_result.scalar_one_or_none()
            if assessment:
                assessment.ml_score = state.get("ml_score", assessment.ml_score)
                assessment.ml_confidence = state.get("ml_confidence", assessment.ml_confidence)
                assessment.decision = state.get("decision", assessment.decision)
                assessment.llm_rationale = state.get("decision_rationale", assessment.llm_rationale)
                session.add(assessment)

        await session.commit()

    return {
        "recommendations": recs,
        "status": "completed",
    }
