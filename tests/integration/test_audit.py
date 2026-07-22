from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.database.postgres import AuditLogModel, async_session_factory
from backend.services.audit_service import log_audit


@pytest.mark.asyncio
async def test_log_audit_entry():
    app_id = None
    await log_audit(
        application_id=app_id,
        action="test_action",
        actor="test_user",
        details={"key": "value"},
        ip_address="127.0.0.1",
    )

    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditLogModel).where(AuditLogModel.application_id == app_id)
        )
        entry = result.scalar_one_or_none()
        assert entry is not None
        assert entry.action == "test_action"
        assert entry.actor == "test_user"
        assert entry.details == {"key": "value"}
        assert entry.ip_address == "127.0.0.1"
