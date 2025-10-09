from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
import uvicorn

from .models.events import Event, EventResponse
from .models.errors import ErrorResponse, ErrorType
from .core.config import settings
from .core.logging import get_logger, setup_logging
from .core.middleware import request_context_middleware
from .core.event_processor import EventProcessor

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HLR/HSS Connector Microservice",
    description="Processes PortaBilling ESPF events (post-NSPS) and syncs with HLR/HSS Core system",
    version="1.0.0",
)

# Security scheme
security = HTTPBearer()

# Add middleware
app.middleware("http")(request_context_middleware)

# Create event processor instance
event_processor = EventProcessor()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "Healthy", "service": "WTL HLR/HSS Connector"}


@app.post(
    "/process-event",
    dependencies=[Depends(verify_token)],
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {
            "model": EventResponse,
            "description": "Event accepted for processing",
            "content": {
                "application/json": {
                    "example": {"message": "Event accepted for processing"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Invalid access token",
                        "error": "Unauthorized",
                        "type": ErrorType.AUTHENTICATION_ERROR,
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Resource not found",
                        "error": "Not found",
                        "type": ErrorType.VALIDATION_ERROR,
                    }
                }
            },
        },
        405: {
            "model": ErrorResponse,
            "description": "Method not allowed",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Method not allowed",
                        "error": "Method not allowed",
                        "type": ErrorType.VALIDATION_ERROR,
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Validation failed",
                        "error": "Validation failed",
                        "type": ErrorType.VALIDATION_ERROR,
                    }
                }
            },
        },
        429: {
            "model": ErrorResponse,
            "description": "Too many requests",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Too many requests to API Core",
                        "error": "Rate limit exceeded",
                        "type": ErrorType.RATE_LIMIT_ERROR,
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "message": "API Core HTTP error",
                        "error": "Internal server error",
                        "type": ErrorType.SERVICE_ERROR,
                    }
                }
            },
        },
        503: {
            "model": ErrorResponse,
            "description": "Service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Core service is not available",
                        "error": "Connection timeout",
                        "type": ErrorType.CONNECTION_ERROR,
                    }
                }
            },
        },
    },
)
async def process_event(event_data: Event):
    """Process incoming PortaBilling ESPF event that has already been processed by NSPS"""
    try:
        return event_processor.process_event(event_data)
    except ValidationError as e:
        error_response = {"errors": e.errors()}
        logger.error(f"Validation error: {error_response}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_response
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )
