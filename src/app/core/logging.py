import logging
import sys
from typing import Optional

import structlog
from typing_extensions import Literal


def configure_logging(
    log_level: str | None = None, log_format: Literal["json", "console"] | None = None
) -> None:
    """
    Configure stdlib logging and structlog with a selectable renderer.

    If log_level or log_format are not provided, fall back to app settings.
    """
    from app.core.config import settings  # Imported here to avoid circular imports

    resolved_log_level = log_level or settings.app.log_level
    resolved_log_format = log_format or settings.app.log_format

    logging.basicConfig(
        level=resolved_log_level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Reduce SQLAlchemy noise
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # Reduce aio_pika/aiormq noise
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)

    common_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.dict_tracebacks,
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if resolved_log_format == "console"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*common_processors, renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
