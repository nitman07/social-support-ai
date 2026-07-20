import json
import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    """Forward standard library logging to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_name == "<module>":
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: str = "DEBUG", log_file: str | None = None) -> None:
    """Configure structured logging with Loguru.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs to stdout only.
    """
    logger.remove()

    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=format_string,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            format=format_string,
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=False,
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

    logger.info("Logging configured", level=log_level, file=log_file)


class CorrelationIdFilter:
    """Add correlation ID to all log records."""

    def __init__(self, correlation_id: str = "") -> None:
        self.correlation_id = correlation_id

    def __call__(self, record: "logging.LogRecord") -> bool:
        record.correlation_id = self.correlation_id
        return True


def get_logger(name: str) -> logger:  # type: ignore[no-any-unimported]
    """Get a Loguru logger instance with the given name.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing application", application_id="...")
    """
    return logger.bind(module=name)


class JSONFormatter:
    """Format log records as JSON for production log aggregation."""

    def __call__(self, record: dict[str, Any]) -> str:
        log_entry = {
            "timestamp": record.get("time", ""),
            "level": record.get("level", ""),
            "module": record.get("name", ""),
            "function": record.get("function", ""),
            "line": record.get("line", ""),
            "message": record.get("message", ""),
        }

        extra = record.get("extra", {})
        if extra:
            log_entry["extra"] = extra

        exception = record.get("exception")
        if exception:
            log_entry["exception"] = str(exception)

        return json.dumps(log_entry, default=str)


def enable_json_logging() -> None:
    """Switch to JSON log format (for production deployments)."""
    logger.remove()
    logger.add(
        sys.stdout,
        format=JSONFormatter(),
        level="INFO",
        colorize=False,
    )
