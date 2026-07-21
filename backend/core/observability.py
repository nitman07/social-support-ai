from datetime import datetime, timezone
from functools import wraps
from typing import Any

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

_langfuse = None


def get_langfuse():
    global _langfuse
    if _langfuse is None:
        try:
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                from langfuse import Langfuse
                _langfuse = Langfuse(
                    host=settings.langfuse_host,
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                )
                logger.info("LangFuse initialized")
            else:
                logger.info("LangFuse not configured (keys empty)")
        except Exception as e:
            logger.warning(f"LangFuse initialization failed: {e}")
    return _langfuse


def trace_node(name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(state: dict, *args, **kwargs) -> dict:
            lf = get_langfuse()
            trace = None
            if lf:
                try:
                    trace = lf.trace(
                        name=f"node_{name}",
                        input={"application_id": state.get("application_id")},
                    )
                except Exception:
                    trace = None
            start = datetime.now(timezone.utc)
            try:
                result = await func(state, *args, **kwargs)
                duration = (datetime.now(timezone.utc) - start).total_seconds()
                if trace:
                    trace.update(output=result)
                logger.info(f"Node '{name}' completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now(timezone.utc) - start).total_seconds()
                if trace:
                    trace.update(output={"error": str(e)}, status="error")
                logger.error(f"Node '{name}' failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator
