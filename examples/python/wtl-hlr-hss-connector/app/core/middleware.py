import time
import uuid
from datetime import datetime, timezone
from fastapi import Request
from .logging import (
    get_logger,
    REQUEST_ID_VAR,
    REQUEST_ID_HEADER,
    UNIQUE_ID_VAR,
    UNIQUE_ID_HEADER,
)

logger = get_logger(__name__)


def set_request_context(request: Request):
    """Set request context variables"""
    REQUEST_ID_VAR.set(request.headers.get(REQUEST_ID_HEADER, uuid.uuid4().hex[:16]))
    UNIQUE_ID_VAR.set(request.headers.get(UNIQUE_ID_HEADER, uuid.uuid4().hex[:16]))


async def request_context_middleware(request: Request, call_next):
    """Middleware to set request context and log HTTP requests"""
    # Set request context
    set_request_context(request)

    # Log incoming request
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Log request completion
    process_time = time.time() - start_time

    # Structure HTTP request log similar to JSONRequestHandler
    logger.info(
        "HTTP request completed",
        extra={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "remote_addr": request.client.host if request.client else "unknown",
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.url.query) if request.url.query else "",
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
            "user_agent": request.headers.get("user-agent", ""),
        }
    )

    return response