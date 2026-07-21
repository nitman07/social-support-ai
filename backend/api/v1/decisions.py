import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from backend.api.v1.auth import get_current_user
from backend.api.v1.schemas import (
    ApplicationDetail,
    FlagResolveRequest,
    SignoffRequest,
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
from backend.workflows.graph import application_graph

logger = get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["Decisions"])


@router.get("/{application_id}/flags")
async def get_flags(application_id: uuid.UUID, user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        result = await session.execute(
            select(InconsistencyModel)
            .where(InconsistencyModel.application_id == application_id)
            .order_by(InconsistencyModel.severity.desc())
        )
        flags = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "field": f.field,
            "source_a": f.source_a,
            "value_a": f.value_a,
            "source_b": f.source_b,
            "value_b": f.value_b,
            "severity": f.severity,
            "status": f.status,
            "created_at": f.created_at.isoformat(),
        }
        for f in flags
    ]


@router.post("/{application_id}/resolve-flag/{flag_id}")
async def resolve_flag(
    application_id: uuid.UUID,
    flag_id: uuid.UUID,
    request: FlagResolveRequest,
    user: dict = Depends(get_current_user),
):
    async with async_session_factory() as session:
        flag = await session.get(InconsistencyModel, flag_id)
        if not flag or flag.application_id != application_id:
            raise HTTPException(status_code=404, detail="Flag not found")

        flag.status = request.action
        session.add(flag)
        await session.commit()

    return {"status": "ok", "message": f"Flag {request.action}"}


@router.post("/{application_id}/signoff")
async def signoff_application(
    application_id: uuid.UUID,
    request: SignoffRequest,
    user: dict = Depends(get_current_user),
):
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        app.status = request.decision
        session.add(app)

        assess_result = await session.execute(
            select(AssessmentModel)
            .where(AssessmentModel.application_id == application_id)
            .limit(1)
        )
        assessment = assess_result.scalar_one_or_none()
        if assessment:
            assessment.decision = request.decision
            assessment.decision_reason = request.rationale
            assessment.decided_by = user.get("user_id", "human")
            assessment.decided_at = datetime.now(timezone.utc)
            session.add(assessment)

        await session.commit()

    return {"status": "ok", "message": f"Application {request.decision}"}


@router.post("/{application_id}/resume")
async def resume_workflow(application_id: uuid.UUID, user: dict = Depends(get_current_user)):
    async with async_session_factory() as session:
        app = await session.get(ApplicationModel, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        if app.status != "awaiting_review":
            raise HTTPException(status_code=409, detail="Application is not awaiting review")

        app.status = "processing"
        session.add(app)
        await session.commit()
        workflow_id = app.workflow_id

    import asyncio
    asyncio.create_task(_resume_workflow(str(application_id), workflow_id or ""))

    return {"status": "ok", "message": "Workflow resumed"}


async def _resume_workflow(application_id: str, workflow_id: str) -> None:
    try:
        config = {"configurable": {"thread_id": workflow_id}}
        state = await application_graph.aget_state(config)
        if state:
            await application_graph.aupdate_state(config, {"status": "processing"})
        logger.info(f"Workflow {workflow_id} resumed")
    except Exception as e:
        logger.error(f"Failed to resume workflow {workflow_id}: {e}")
