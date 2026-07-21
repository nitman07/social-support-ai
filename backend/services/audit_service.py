from datetime import datetime, timezone
from uuid import UUID

from backend.core.logging import get_logger
from backend.database.postgres import AuditLogModel, async_session_factory

logger = get_logger(__name__)


async def log_audit(
    application_id: UUID | str | None,
    action: str,
    actor: str = "system",
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    if isinstance(application_id, str):
        application_id = UUID(application_id)
    try:
        async with async_session_factory() as session:
            entry = AuditLogModel(
                application_id=application_id,
                action=action,
                actor=actor,
                details=details or {},
                ip_address=ip_address,
                created_at=datetime.now(timezone.utc),
            )
            session.add(entry)
            await session.commit()
        logger.debug(f"Audit: {action} by {actor}")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
