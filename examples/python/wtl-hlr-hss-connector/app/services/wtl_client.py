from typing import TypeVar
import httpx
from pydantic import BaseModel
from http import HTTPStatus

from ..core.config import settings
from ..core.logging import get_logger
from ..models.wtl import WTLResponse
from ..models.errors import ErrorType, ErrorResponse

logger = get_logger(__name__)

# Generic type for request models
RequestT = TypeVar("RequestT", bound=BaseModel)


class WTLClient:
    """Client for WTL HLR/HSS API"""

    def __init__(self):
        self.base_url = settings.WTL_API_URL.rstrip("/")
        self.token = settings.WTL_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, request: RequestT, endpoint: str = "/prov") -> WTLResponse:
        """Make request to WTL API with retry logic"""
        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(
                timeout=settings.WTL_HTTP_REQUESTS_TIMEOUT,
                headers=self.headers,
            ) as client:
                response = client.post(url, json=request.model_dump(exclude_none=True))
                response.raise_for_status()

                wtl_response = WTLResponse.model_validate(response.json())

                if not wtl_response.is_successful:
                    logger.error(
                        "WTL API request failed",
                        extra={
                            "error": wtl_response.error,
                            "request": request.model_dump(),
                        },
                    )
                    raise WTLServiceError(
                        message="WTL service error",
                        error=wtl_response.error or "Unknown error",
                    )

                return wtl_response

        except httpx.ReadTimeout as e:
            logger.error("WTL API timeout", error=str(e))
            raise ConnectionError(
                message="WTL service is not available",
                error="Connection timeout",
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "WTL API HTTP error",
                extra={
                    "status_code": e.response.status_code,
                    "error": str(e),
                },
            )
            if e.response.status_code == HTTPStatus.UNAUTHORIZED:
                raise AuthenticationError(
                    message="WTL API authentication failed",
                    error="Invalid API token",
                )
            elif e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError(
                    message="Too many requests to API Core",
                    error="Rate limit exceeded",
                )
            else:
                try:
                    error_data = e.response.json()
                    wtl_response = WTLResponse.model_validate(error_data)
                    error_msg = wtl_response.error or "Unknown error"
                except Exception:
                    error_msg = str(e)

                logger.error(
                    "WTL API request failed",
                    extra={
                        "error": error_msg,
                        "request": request.model_dump(),
                    },
                )
                raise WTLServiceError(
                    message="WTL service error",
                    error=error_msg,
                )

        except Exception as e:
            logger.error("Unexpected error calling WTL API", extra={"error": str(e)})
            raise InternalError(
                message="Internal server error",
                error="Unexpected error occurred",
            )

    def send_request(self, request: RequestT) -> WTLResponse:
        """Send request to WTL API"""
        return self._make_request(request)


# Custom exceptions
class WTLError(Exception):
    """Base exception for WTL API errors"""

    def __init__(
        self,
        message: str,
        error: str,
        error_type: ErrorType,
    ):
        self.error_response = ErrorResponse(
            message=message,
            error=error,
            type=error_type,
        )
        super().__init__(message)


class AuthenticationError(WTLError):
    def __init__(self, message: str, error: str):
        super().__init__(message, error, ErrorType.AUTHENTICATION_ERROR)


class WTLServiceError(WTLError):
    def __init__(self, message: str, error: str):
        super().__init__(message, error, ErrorType.SERVICE_ERROR)


class ConnectionError(WTLError):
    def __init__(self, message: str, error: str):
        super().__init__(message, error, ErrorType.CONNECTION_ERROR)


class RateLimitError(WTLError):
    def __init__(self, message: str, error: str):
        super().__init__(message, error, ErrorType.RATE_LIMIT_ERROR)


class InternalError(WTLError):
    def __init__(self, message: str, error: str):
        super().__init__(message, error, ErrorType.INTERNAL_ERROR)