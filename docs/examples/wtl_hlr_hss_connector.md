### NSPS Python + FastAPI Example: WTL HLR/HSS Connector

This guide walks through building an NSPS connector in Python using FastAPI. It uses the `wtl_hlr_hss_connector-main` implementation as a concrete example. You’ll see how to receive events from NSPS, validate/authenticate requests, enrich and transform payloads, and forward data to an external system (e.g., HLR/HSS Core API or Google Sheets).

- Base implementation: `wtl_hlr_hss_connector-main`
- Language/stack: Python 3.13+, FastAPI, Pydantic, httpx, structlog

Links to referenced source files are provided in each section, and code citations include inline references to exact lines in the repository.

---

### Table of Contents

1. Overview and Flow
2. Project Structure
3. API Surface
   - Health check
   - Process Event endpoint
4. Authentication
5. Request Tracing and Logging
6. Event Model and Validation
7. Event Processing Pipeline
8. External System Integration
   - WTL HLR/HSS (as implemented)
   - Adapting to Google Sheets (how-to)
9. Configuration and Environment
10. Example Requests and Responses
11. Best Practices and Notes
12. Source References

---

### 1) Overview and Flow

- NSPS enriches PortaBilling events and sends them to your connector.
- The connector authenticates requests, parses payloads, extracts relevant fields, and maps them to the external system’s API schema.
- The connector logs details with correlation IDs from request headers for end-to-end traceability.
- The external call’s result determines the response and additional error handling.

High-level sequence:
1. NSPS → POST `/process-event` with Bearer token and JSON body.
2. Connector validates token, parses JSON, and logs with `x-b3-traceid` / `x-request-id`.
3. Connector determines action (e.g., update subscriber), derives IMSI/MSISDN/profiles, and invokes the external API client.
4. Returns 202 for accepted processing, or structured errors for failures.

---

### 2) Project Structure

Key components in `wtl_hlr_hss_connector-main/app`:

- `main.py` — FastAPI app, endpoints, auth dependency
- `core/config.py` — settings via environment variables
- `core/logging.py` — structured logging with request IDs
- `core/middleware.py` — request context and access logging
- `core/event_processor.py` — event processing orchestration
- `services/pb_event.py` — NSPS payload extraction helpers
- `services/wtl_client.py` — external API client (WTL)
- `models/events.py` — Pydantic models for NSPS payload
- `models/wtl.py` — Pydantic models for external API
- `models/errors.py` — common error model/types

---

### 3) API Surface

#### Health check

The health endpoint returns a simple object and can be used by load balancers or for smoke tests.

```py title="wtl_hlr_hss_connector-main/app/main.py" linenums="45"
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "Healthy", "service": "WTL HLR/HSS Connector"}
```

- File: `wtl_hlr_hss_connector-main/app/main.py`

#### Process Event endpoint

Secured POST endpoint for NSPS to deliver enriched events.

```py title="wtl_hlr_hss_connector-main/app/main.py" linenums="51"
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
```

```py title="wtl_hlr_hss_connector-main/app/main.py" linenums="159"
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
```

- File: `wtl_hlr_hss_connector-main/app/main.py`

---

### 4) Authentication

- Bearer token verification is enforced using FastAPI’s `HTTPBearer`.
- The token is compared to `settings.API_TOKEN` (env-configured).

```py title="wtl_hlr_hss_connector-main/app/main.py" linenums="24"
# Security scheme
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
```

- File: `wtl_hlr_hss_connector-main/app/main.py`

---

### 5) Request Tracing and Logging

The connector logs in JSON with `structlog`, including correlation headers:
- `x-b3-traceid` → `request_id`
- `x-request-id` → `unique_id`

Setup and enrichers:

```py title="wtl_hlr_hss_connector-main/app/core/logging.py" linenums="25"
def setup_logging():
    """Setup structured logging for the microservice"""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.value),
    )

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
```

```py title="wtl_hlr_hss_connector-main/app/core/logging.py" linenums="8"
REQUEST_ID_HEADER = "x-b3-traceid"
REQUEST_ID_KEY = "request_id"
REQUEST_ID_VAR: ContextVar[str] = ContextVar(REQUEST_ID_KEY, default="")

UNIQUE_ID_HEADER: str = "x-request-id"
UNIQUE_ID_KEY: str = "unique_id"
UNIQUE_ID_VAR: ContextVar[str] = ContextVar(UNIQUE_ID_KEY, default="")
```

```py title="wtl_hlr_hss_connector-main/app/core/middleware.py" linenums="16"
def set_request_context(request: Request):
    """Set request context variables"""
    REQUEST_ID_VAR.set(request.headers.get(REQUEST_ID_HEADER, uuid.uuid4().hex[:16]))
    UNIQUE_ID_VAR.set(request.headers.get(UNIQUE_ID_HEADER, uuid.uuid4().hex[:16]))
```

```py title="wtl_hlr_hss_connector-main/app/core/middleware.py" linenums="22"
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
```

- Files:
  - `wtl_hlr_hss_connector-main/app/core/logging.py`
  - `wtl_hlr_hss_connector-main/app/core/middleware.py`

---

### 6) Event Model and Validation

The connector expects NSPS-enriched payloads. Models align with the NSPS spec in this repo’s `docs/assets/OpenAPI.json`.

Event and nested models:

```py title="wtl_hlr_hss_connector-main/app/models/events.py" linenums="351"
class ESPFEvent(BaseModel):
    """Model representing incoming ESPF event"""
    event_type: str = Field(
        description="The type of the event",
        examples=["SIM/Updated"]
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="All event variables passed as-is from original event",
    )


class Event(BaseModel):
    """Main event model"""
    event_id: str = Field(
        description="Unique identifier of the event",
        examples=["a3623086-24c2-47fb-a17f-929d9e542ed2"]
    )
    data: ESPFEvent = Field(
        description="Event data containing type and variables"
    )
    handler_id: Optional[str] = Field(
        None,
        description="ID of the handler processing this event",
        examples=["wtl"]
    )
    created_at: Optional[str] = Field(
        None,
        description="When the event was created (ISO datetime string)",
        examples=["2025-06-09T17:44:21.207629+00:00"]
    )
    updated_at: Optional[str] = Field(
        None,
        description="When the event was last updated (ISO datetime string)",
        examples=["2025-06-09T17:44:22.125109+00:00"]
    )
    status: Optional[str] = Field(
        None,
        description="Current status of the event",
        examples=["queued"]
    )
    pb_data: Optional[PBData] = Field(
        None,
        description="Simplified PortaBilling data with only essential fields"
    )
```

- File: `wtl_hlr_hss_connector-main/app/models/events.py`

Refer to `docs/index.md` and `docs/assets/OpenAPI.json` in this repository for field-level descriptions and examples.

---

### 7) Event Processing Pipeline

The orchestration:

```py title="wtl_hlr_hss_connector-main/app/core/event_processor.py" linenums="12"
class EventProcessor:
    def __init__(self):
        self.wtl_client = WTLClient()

    def process_event(self, event_data):
        """Process incoming PortaBilling ESPF event"""
        try:
            processor = PortaBillingEventProcessor(event=event_data)

            logger.info(f"Received event: {event_data.event_id}, type: {event_data.data.event_type}")

            action = EventWTLActionMapper(
                event_type=processor.get_event_type()
            ).action

            if not action:
                message = f"No defined action for event type: {processor.get_event_type()}"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )
```

IMSI and constraints:

```py title="wtl_hlr_hss_connector-main/app/core/event_processor.py" linenums="35"
            imsi = processor.get_imsi_from_sim_info()
            if not imsi:
                message = "IMSI is empty or not provided"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )

            if not processor.validate_imsi_using_regex(imsi):
                message = f"IMSI {imsi} doesn't follow the regexp provided"
                logger.warning(message)
                return JSONResponse(
                    content={"message": f"Event ignored: {message}"},
                    status_code=status.HTTP_202_ACCEPTED
                )
```

Deriving MSISDN, subscriber status, and unified request:

```py title="wtl_hlr_hss_connector-main/app/core/event_processor.py" linenums="52"
            msisdn_list = []
            if processor.get_bill_status() == BillStatus.OPEN.value:
                msisdn_list = [processor.get_account_id()]

            subscriber_status = SubscriberStatus.OPERATOR_DETERMINED_BARRING.value
            if (
                not processor.get_block_status()
                and processor.get_bill_status() == BillStatus.OPEN.value
            ):
                subscriber_status = SubscriberStatus.SERVICE_GRANTED.value

            # Create and send unified request
            request_data = UnifiedSyncRequest(
                imsi=imsi,
                subscriber_status=subscriber_status,
                msisdn=msisdn_list,
                cs_profile=processor.get_cs_profile(),
                eps_profile=processor.get_eps_profile(),
                action=action,
            )

            logger.info(
                "Sending unified sync request",
                extra={
                    "event_id": event_data.event_id,
                    "imsi": request_data.imsi,
                    "status": request_data.subscriber_status,
                    "msisdn": request_data.msisdn,
                    "cs_profile": request_data.cs_profile,
                    "eps_profile": request_data.eps_profile,
                    "action": action,
                },
            )

            self.wtl_client.send_request(request_data)
            return JSONResponse(
                content={"message": "Event processed successfully"},
                status_code=status.HTTP_202_ACCEPTED
            )
```

Error handling:

```py title="wtl_hlr_hss_connector-main/app/core/event_processor.py" linenums="92"
        except WTLError as e:
            logger.error(f"WTL error: {e.error_response.error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.error_response.model_dump()
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Internal server error", "error": str(e)}
            )
```

- File: `wtl_hlr_hss_connector-main/app/core/event_processor.py`

NSPS payload helpers:

```py title="wtl_hlr_hss_connector-main/app/services/pb_event.py" linenums="11"
class PortaBillingEventProcessor:
    """PortaBilling Event processing"""

    def __init__(self, event: Event):
        self.event = event
        self.account_info = self.event and self.event.pb_data and self.event.pb_data.account_info
        self.access_policy_info = self.event and self.event.pb_data and self.event.pb_data.access_policy_info
        self.sim_info = self.event and self.event.pb_data and self.event.pb_data.sim_info

    def get_event_type(self) -> str:
        return self.event and self.event.data and self.event.data.event_type

    def get_imsi_from_sim_info(self) -> str:
        return self.sim_info and self.sim_info.imsi

    def validate_imsi_using_regex(self, imsi: str) -> bool:
        if settings.WTL_IMSI_REGEXP and not re.search(settings.WTL_IMSI_REGEXP, imsi):
            return False
        return True
```

```py title="wtl_hlr_hss_connector-main/app/services/pb_event.py" linenums="31"
    def get_account_id(self) -> Optional[str]:
        if not self.account_info:
            return None
        account_id = self.account_info.id
        return account_id.split("@msisdn")[0] if "@msisdn" in account_id else None

    def get_bill_status(self) -> Optional[BillStatus]:
        return self.account_info and self.account_info.bill_status

    def get_block_status(self) -> Optional[bool]:
        return self.account_info and self.account_info.blocked
```

```py title="wtl_hlr_hss_connector-main/app/services/pb_event.py" linenums="52"
    def _get_profile(self, profile_name: str, default_value: str) -> str:
        policy_info = self.access_policy_info
        if policy_info:
            profile = self._get_profile_value(policy_info.attributes, profile_name)
            if profile:
                return profile

        logger.info(
            f"Using default {profile_name} profile",
            extra={
                "event_id": self.event.event_id,
                "profile": default_value,
            },
        )
        return default_value

    def get_cs_profile(self) -> str:
        return self._get_profile("cs_profile", settings.WTL_DEFAULT_CS_PROFILE)

    def get_eps_profile(self) -> str:
        return self._get_profile("eps_profile", settings.WTL_DEFAULT_EPS_PROFILE)
```

- File: `wtl_hlr_hss_connector-main/app/services/pb_event.py`

---

### 8) External System Integration

#### WTL HLR/HSS (as implemented)

The example integrates with a mock HLR/HSS “WTL” API using httpx.

```py title="wtl_hlr_hss_connector-main/app/services/wtl_client.py" linenums="17"
class WTLClient:
    """Client for WTL HLR/HSS API"""

    def __init__(self):
        self.base_url = settings.WTL_API_URL.rstrip("/")
        self.token = settings.WTL_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
```

```py title="wtl_hlr_hss_connector-main/app/services/wtl_client.py" linenums="28"
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
```

Error mapping (HTTP→domain-specific):

```py title="wtl_hlr_hss_connector-main/app/services/wtl_client.py" linenums="64"
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
```

- File: `wtl_hlr_hss_connector-main/app/services/wtl_client.py`

Request schema to WTL:

```py title="wtl_hlr_hss_connector-main/app/models/wtl.py" linenums="81"
class StatusSyncRequest(WTLBaseRequest):
    """Request model for subscriber status synchronization"""

    subscriber_status: SubscriberStatus


class UnifiedSyncRequest(MSISDNList, ServiceProfile, StatusSyncRequest):
    """Request model for unified synchronization"""

    action: WTLProvAction = Field(
        default=WTLProvAction.UPDATE,
        title="Provisioning action",
    )
```

- File: `wtl_hlr_hss_connector-main/app/models/wtl.py`

#### Adapting to Google Sheets (how-to)

This repository integrates an HLR/HSS API, but the same mechanisms apply to Google Sheets. Replace the `WTLClient` with a `SheetsClient`:

- Use `gspread` or Google Sheets API via `google-api-python-client`.
- Authenticate with a Service Account JSON credential; inject path or JSON via env.
- Model a request similar to `UnifiedSyncRequest` but mapped to sheet rows/columns.
- Implement retries and error mapping analogous to `WTLClient`.

Example of a minimal Sheets client (new code, not in repo):

```python
# Proposed example – not in repository
import gspread
from google.oauth2.service_account import Credentials

class SheetsClient:
    def __init__(self, creds_json: str, spreadsheet_id: str, sheet_name: str):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        gc = gspread.authorize(creds)
        self.sheet = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)

    def append_event(self, event_row: list[str]) -> None:
        # e.g., [event_id, event_type, imsi, msisdn, cs_profile, eps_profile, status]
        self.sheet.append_row(event_row, value_input_option="RAW")
```

Integration point: swap `WTLClient` usage in `EventProcessor` with `SheetsClient.append_event(...)` to push data to a spreadsheet instead of calling an HTTP API.

---

### 9) Configuration and Environment

Settings with defaults and env bindings:

```py title="wtl_hlr_hss_connector-main/app/core/config.py" linenums="16"
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
```

- File: `wtl_hlr_hss_connector-main/app/core/config.py`

For Google Sheets integration, add env vars such as:
- `GOOGLE_SERVICE_ACCOUNT_JSON` (or path)
- `GOOGLE_SPREADSHEET_ID`
- `GOOGLE_SHEET_NAME`

---

### 10) Example Requests and Responses

Health check:

```bash
curl https://[TAG---]SERVICE_NAME-PROJECT_NUMBER.REGION.run.app/health
```

Successful response:
```json
{ "status": "Healthy", "service": "WTL HLR/HSS Connector" }
```

NSPS event delivery (from this repo’s testing section):

```bash
curl -X POST https://[TAG---]SERVICE_NAME-PROJECT_NUMBER.REGION.run.app/process-event \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "3e84c79f-ab6f-4546-8e27-0b6ab866f1fb",
    "data": {
      "event_type": "SIM/Updated",
      "variables": {
        "i_env": 1,
        "i_event": 999999,
        "i_account": 1,
        "curr_status": "used",
        "prev_status": "active"
      }
    },
    "pb_data": {
      "account_info": {
        "bill_status": "open",
        "billing_model": "credit_account",
        "blocked": false,
        "firstname": "Serhii",
        "i_account": 1,
        "i_customer": 6392,
        "i_product": 3774,
        "id": "79123456789@msisdn",
        "lastname": "Dolhopolov",
        "phone1": "",
        "product_name": "Pay as you go",
        "time_zone_name": "Europe/Prague",
        "assigned_addons": [
          {
            "addon_effective_from": "2025-05-16T12:59:46",
            "addon_priority": 10,
            "description": "",
            "i_product": 3775,
            "i_vd_plan": 1591,
            "name": "Youtube UHD"
          }
        ],
        "service_features": [
          {
            "name": "netaccess_policy",
            "effective_flag_value": "Y",
            "attributes": [
              {
                "name": "access_policy",
                "effective_value": "179"
              }
            ]
          }
        ]
      },
      "sim_info": {
        "i_sim_card": 3793,
        "imsi": "001010000020349",
        "msisdn": "79123456789",
        "status": "active"
      },
      "access_policy_info": {
        "i_access_policy": 179,
        "name": "Integration test",
        "attributes": [
          { "group_name": "lte.wtl", "name": "cs_profile", "value": "cs-pp-20250319" },
          { "group_name": "lte.wtl", "name": "eps_profile", "value": "eps-pp-20250319" }
        ]
      }
    },
    "handler_id": "hlr-hss-nsps",
    "created_at": "2025-03-12T16:47:30.443939+00:00",
    "updated_at": "2025-03-12T16:47:36.585885+00:00",
    "status": "received"
  }'
```

Expected responses:
- 202 Accepted: `{ "message": "Event processed successfully" }`
- 401 Unauthorized: `{ "message": "Invalid access token", "error": "Unauthorized", "type": "authentication_error" }`
- 422 Validation errors mapped from external API adapter
- 429 / 500 / 503: As defined in `responses` of the endpoint

---

### 11) Best Practices and Notes

- **Authentication**: 
  - Keep `API_TOKEN` in a secret manager or CI/CD environment variable; rotate periodically.
- **Validation**: 
  - Use Pydantic models for both inbound (NSPS) and outbound (External).
  - Use regex constraints for identifiers (e.g., IMSI) using env-configured patterns.
- **Logging**: 
  - Log in JSON with correlation IDs; include `event_id`, IMSI, action, profiles, and outcome.
  - Never log sensitive tokens or PII beyond what’s necessary for debugging.
- **Error handling**: 
  - Map HTTP errors to domain-level error types; return structured errors to NSPS.
  - For transient errors (timeouts), consider retries with backoff in clients.
- **Observability**: 
  - Add metrics (request count, success/failure, latency) where applicable.
- **Idempotency**: 
  - If external systems are stateful, consider deduplicating by `event_id` to avoid re-application.
- **Google Sheets**: 
  - Batch writes where possible.
  - Validate rate limits and handle quota errors explicitly.
  - Use service accounts and restricted scopes.

---

---

### Source References

- `wtl_hlr_hss_connector-main/app/main.py`
- `wtl_hlr_hss_connector-main/app/core/config.py`
- `wtl_hlr_hss_connector-main/app/core/logging.py`
- `wtl_hlr_hss_connector-main/app/core/middleware.py`
- `wtl_hlr_hss_connector-main/app/core/event_processor.py`
- `wtl_hlr_hss_connector-main/app/services/pb_event.py`
- `wtl_hlr_hss_connector-main/app/services/wtl_client.py`
- `wtl_hlr_hss_connector-main/app/models/events.py`
- `wtl_hlr_hss_connector-main/app/models/wtl.py`
- `wtl_hlr_hss_connector-main/app/models/errors.py`

---

This example demonstrates the core mechanics of an NSPS connector in Python + FastAPI. You can substitute the external adapter (WTL) with a Google Sheets adapter by implementing a similar client, preserving authentication, logging, error mapping, and payload transformation patterns.


