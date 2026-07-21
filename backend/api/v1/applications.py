import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from backend.api.v1.auth import get_current_user
from backend.api.v1.schemas import (
    ApplicationDetail,
    ApplicationListItem,
    ApplicationListResponse,
    AssessmentResponse,
    DocumentResponse,
    InconsistencyResponse,
    ProcessResponse,
    RecommendationResponse,
    WorkflowStatusResponse,
)
from backend.core.logging import get_logger
from backend.database.postgres import (
    ApplicantModel,
    ApplicationModel,
    AssessmentModel,
    DocumentModel,
    InconsistencyModel,
    RecommendationModel,
    async_session_factory,
)
from backend.ml.model import ml_service
from backend.services.audit_service import log_audit
from backend.workflows.graph import application_graph
from backend.workflows.state import ApplicationState

logger = get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    async with async_session_factory() as session:
        query = select(ApplicationModel, ApplicantModel.full_name).join(
            ApplicantModel, ApplicationModel.applicant_id == ApplicantModel.id
        )
        count_query = select(func.count(ApplicationModel.id))

        if status:
            query = query.where(ApplicationModel.status == status)
            count_query = count_query.where(ApplicationModel.status == status)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        result = await session.execute(
            query.order_by(ApplicationModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.fetchall()

    items = [
        ApplicationListItem(
            id=row.ApplicationModel.id,
            applicant_name=row.full_name,
            status=row.ApplicationModel.status,
            submitted_at=row.ApplicationModel.submitted_at,
            created_at=row.ApplicationModel.created_at,
        )
        for row in rows
    ]
    return ApplicationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(application_id: uuid.UUID, user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        applicant = await session.get(ApplicantModel, app.applicant_id)

        docs_result = await session.execute(
            select(DocumentModel).where(DocumentModel.application_id == application_id)
        )
        docs = docs_result.scalars().all()

        assess_result = await session.execute(
            select(AssessmentModel)
            .where(AssessmentModel.application_id == application_id)
            .limit(1)
        )
        assessment = assess_result.scalar_one_or_none()

        inc_result = await session.execute(
            select(InconsistencyModel)
            .where(InconsistencyModel.application_id == application_id)
        )
        inconsistencies = inc_result.scalars().all()

        recs_result = None
        if assessment:
            recs_result = await session.execute(
                select(RecommendationModel)
                .where(RecommendationModel.assessment_id == assessment.id)
            )

    return ApplicationDetail(
        id=app.id,
        applicant={
            "id": applicant.id,
            "full_name": applicant.full_name,
            "emirates_id": applicant.emirates_id,
            "nationality": applicant.nationality,
        },
        status=app.status,
        workflow_id=app.workflow_id,
        documents=[
            DocumentResponse(
                id=d.id, document_type=d.document_type, file_name=d.file_name,
                ocr_status=d.ocr_status, ocr_confidence=d.ocr_confidence,
            ) for d in docs
        ],
        assessment=AssessmentResponse(
            id=assessment.id, ml_score=assessment.ml_score,
            ml_confidence=assessment.ml_confidence, decision=assessment.decision,
            llm_rationale=assessment.llm_rationale,
            decided_by=assessment.decided_by,
        ) if assessment else None,
        inconsistencies=[
            InconsistencyResponse(
                id=i.id, field=i.field, source_a=i.source_a, value_a=i.value_a,
                source_b=i.source_b, value_b=i.value_b, severity=i.severity,
                status=i.status,
            ) for i in inconsistencies
        ],
        recommendations=[
            RecommendationResponse(
                id=r.id, category=r.category, title=r.title,
                description=r.description, relevance_score=r.relevance_score,
            ) for r in (recs_result.scalars().all() if recs_result else [])
        ] if assessment else [],
        submitted_at=app.submitted_at,
        created_at=app.created_at,
    )


@router.post("/{application_id}/process", response_model=ProcessResponse, status_code=202)
async def process_application(application_id: uuid.UUID, user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        if app.status == "processing":
            raise HTTPException(status_code=409, detail="Application already processing")

        app.status = "processing"
        app.workflow_id = f"wf_{application_id.hex[:8]}"
        session.add(app)
        await session.commit()
        workflow_id = app.workflow_id

    await log_audit(
        application_id=application_id,
        action="workflow_started",
        actor=user.get("user_id", "system"),
    )

    import asyncio
    asyncio.create_task(_run_workflow(str(application_id), workflow_id))

    return ProcessResponse(
        application_id=application_id,
        workflow_id=workflow_id,
        message="Workflow started",
    )


@router.get("/{application_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(application_id: uuid.UUID, user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        assessment = None
        if app.status in ("approved", "declined", "completed"):
            assess_result = await session.execute(
                select(AssessmentModel)
                .where(AssessmentModel.application_id == application_id)
                .limit(1)
            )
            assessment = assess_result.scalar_one_or_none()

    return WorkflowStatusResponse(
        application_id=application_id,
        status=app.status,
        workflow_id=app.workflow_id,
        decision=assessment.decision if assessment else None,
        ml_score=assessment.ml_score if assessment else None,
        requires_human_review=app.status == "awaiting_review",
        errors=[],
    )


async def _run_workflow(application_id: str, workflow_id: str) -> None:
    try:
        await ml_service.load_model()

        initial_state: ApplicationState = {
            "application_id": application_id,
            "applicant_id": "",
            "status": "processing",
            "workflow_id": workflow_id,
            "documents": [],
            "ocr_results": {},
            "extraction_complete": False,
            "validated_data": {},
            "inconsistencies": [],
            "validation_complete": False,
            "requires_human_review": False,
            "retrieved_policies": [],
            "ml_features": {},
            "ml_score": None,
            "ml_confidence": None,
            "ml_feature_importance": {},
            "eligibility_rules_applied": [],
            "decision": None,
            "decision_rationale": None,
            "decision_confidence": 0.0,
            "recommendations": [],
            "errors": [],
            "retry_count": 0,
        }
        config = {"configurable": {"thread_id": workflow_id}}
        await application_graph.ainvoke(initial_state, config=config)
        logger.info(f"Workflow {workflow_id} completed")
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        async with async_session_factory() as session:
            app = await session.get(ApplicationModel, application_id)
            if app:
                app.status = "failed"
                session.add(app)
                await session.commit()
