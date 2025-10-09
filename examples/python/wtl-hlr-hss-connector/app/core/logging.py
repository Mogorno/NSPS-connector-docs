import logging
import sys
import structlog
from contextvars import ContextVar

from .config import settings

# Context variables for request tracking
REQUEST_ID_HEADER = "x-b3-traceid"
REQUEST_ID_KEY = "request_id"
REQUEST_ID_VAR: ContextVar[str] = ContextVar(REQUEST_ID_KEY, default="")

UNIQUE_ID_HEADER: str = "x-request-id"
UNIQUE_ID_KEY: str = "unique_id"
UNIQUE_ID_VAR: ContextVar[str] = ContextVar(UNIQUE_ID_KEY, default="")


def add_request_ids(logger, method_name, event_dict):
    """Add request_id and unique_id from contextvars to log event dict"""
    event_dict[REQUEST_ID_KEY] = REQUEST_ID_VAR.get("")
    event_dict[UNIQUE_ID_KEY] = UNIQUE_ID_VAR.get("")
    return event_dict


def setup_logging():
    """Setup structured logging for the microservice"""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.value),
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        add_request_ids,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.EventRenamer(to="message"),
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance"""
    return structlog.get_logger(name)