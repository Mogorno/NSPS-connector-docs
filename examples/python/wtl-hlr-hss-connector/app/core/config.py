from enum import Enum
from typing import Optional
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = Field(default="wtl-hlr-hss-connector", description="Demo WTL HLR HSS Connector")
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    PORT: int = Field(default=8000, description="Port to run the application on")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Authentication
    API_TOKEN: str = Field(
        ...,
        description="Bearer token required for authenticating API requests in this application",
    )

    # WTL API settings
    WTL_API_URL: str = Field(
        ...,
        description="The base URL for accessing the WTL system's API endpoints",
        examples=["http://localhost:3001/wtl/hlr/v1"],
    )
    WTL_API_TOKEN: str = Field(
        ..., description="Authentication token used to access the WTL API securely"
    )
    WTL_DEFAULT_CS_PROFILE: str = Field(
        "default",
        title="Default CS Profile",
        description="The default CS profile that is used if not specified in the access_policy",
    )
    WTL_DEFAULT_EPS_PROFILE: str = Field(
        "default",
        title="Default EPS Profile",
        description="The default EPS profile that is used if not specified in the access_policy",
    )
    WTL_HTTP_REQUESTS_TIMEOUT: float = Field(
        30.0,
        description="HTTP timeout of requests to the WTL system",
        title="HTTP timeout",
    )

    # IMSI validation
    WTL_IMSI_REGEXP: Optional[str] = Field(
        None,
        description="A Python-compatible regex pattern (using 're.search()'). "
        "Ensure it follows Python's 're' module syntax.",
        examples=["^(90170000005017[0-9]|90170000005018[0-9]|00101000002034[1-9])$"],
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()