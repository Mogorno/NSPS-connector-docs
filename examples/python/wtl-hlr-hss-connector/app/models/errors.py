from enum import Enum
from pydantic import BaseModel


class ErrorType(str, Enum):
    """Error types for the application"""

    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    SERVICE_ERROR = "service_error"
    CONNECTION_ERROR = "connection_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INTERNAL_ERROR = "internal_error"


class ErrorResponse(BaseModel):
    """Standard error response model"""

    message: str
    error: str
    type: ErrorType