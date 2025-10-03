# Connector Flow Explained

## 1. Accept request

The microservice exposes a single POST endpoint at `/process-event` using FastAPI. This endpoint is designed to be minimal, delegating all business logic to a processor function. The endpoint expects a JSON payload matching the `Event` schema and is protected by authentication (see next step). The handler simply receives the validated event data and passes it to the event processor, which orchestrates the rest of the workflow.

```py title="app/main.py" linenums="18"
app = FastAPI(
    title="HLR/HSS Connector Microservice",
    description="Processes PortaBilling ESPF events (post-NSPS) and syncs with HLR/HSS Core system",
    version="1.0.0",
)
```

```py title="app/main.py" linenums="51"
@app.post(
    "/process-event",
    dependencies=[Depends(verify_token)],
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_event(event_data: Event):
    return event_processor.process_event(event_data)
```

[View source: `app/main.py`][app/main.py]

---

## 2. Enforce Bearer auth

Authentication is handled by a dependency (`Depends(verify_token)`) that checks for a valid Bearer token in the request. The `verify_token` function compares the provided token to a value stored in environment variables. If the token is missing or incorrect, the function raises an HTTP 401 error with a standard `WWW-Authenticate: Bearer` header, ensuring clients know how to authenticate. This approach centralizes security logic, making it easy to update or reuse across endpoints.

```py title="app/main.py" linenums="24"
security = HTTPBearer()
```

```py title="app/main.py" linenums="34"
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
```

[View source: `app/main.py`][app/main.py]

- Why Bearer here: NSPS authenticates with a shared secret; rotating the token only requires changing env vars.
- Failure behavior: 401 is returned with `WWW-Authenticate: Bearer`, which is standard for API clients.

## 3. Set request context and JSON logging

Before processing each request, middleware sets up tracing context by extracting or generating unique request IDs from headers. This ensures every request is traceable in logs, even if the client does not provide tracing headers. The middleware attaches these IDs to the request context and logs the completion of each HTTP request in structured JSON format, including status codes and timestamps. This makes debugging and monitoring much easier, especially in distributed or cloud environments.

```py title="app/core/middleware.py" linenums="16"
def set_request_context(request: Request):
    REQUEST_ID_VAR.set(request.headers.get(REQUEST_ID_HEADER, uuid.uuid4().hex[:16]))
    UNIQUE_ID_VAR.set(request.headers.get(UNIQUE_ID_HEADER, uuid.uuid4().hex[:16]))
```

```py title="app/core/middleware.py" linenums="22"
async def request_context_middleware(request: Request, call_next):
    set_request_context(request)
    response = await call_next(request)
    logger.info(
        "HTTP request completed",
        extra={"status_code": response.status_code},
    )
    return response
```

[View source: `app/core/middleware.py`][app/core/middleware.py]

- Log shape: JSON via structlog with automatic timestamp and traced IDs.

## 4. Validate payload against schemas

Incoming requests are validated against Pydantic models before any business logic runs. The `Event` model requires an `event_id`, a nested `data` object (with `event_type` and `variables`), and optionally a `pb_data` object. If any required fields are missing or malformed, FastAPI automatically returns a 422 error, making it clear to clients what is wrong with their request. This strict validation ensures that only well-formed data reaches the business logic, reducing the risk of runtime errors.

```py title="app/models/events.py" linenums="363"
class Event(BaseModel):
    event_id: str = Field(
        description="Unique identifier of the event",
        examples=["a3623086-24c2-47fb-a17f-929d9e542ed2"]
    )
    data: ESPFEvent = Field(
        description="Event data containing type and variables"
    )
    pb_data: Optional[PBData] = Field(
        None,
        description="Simplified PortaBilling data with only essential fields"
    )
```

```py title="app/models/events.py" linenums="351"
class ESPFEvent(BaseModel):
    event_type: str = Field(
        description="The type of the event",
        examples=["SIM/Updated"]
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="All event variables passed as-is from original event",
    )
```

[View source: `app/models/events.py`][app/models/events.py]

## 5. Map event_type → WTL action

The connector uses a mapping to translate incoming event types (such as `SIM/Updated`) into specific provisioning actions for the WTL system (like `update`). This mapping is explicit and easy to extend, making it clear which event types are supported. If an unknown event type is received, the system logs the event and returns a 202 response, ensuring that unsupported events do not break the NSPS pipeline. This design makes the connector robust and easy to maintain.

```py title="app/models/wtl.py" linenums="33"
class WTLProvAction(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SET = "set"
    UNSET = "unset"
    MODIFY = "modify"
```

```py title="app/models/wtl.py" linenums="42"
EVENT_ACTION_MAP = {
    EventType.SIM_UPDATED: WTLProvAction.UPDATE,
}
```

```py title="app/models/wtl.py" linenums="47"
class EventWTLActionMapper(BaseModel):
    event_type: str

    @property
    def action(self) -> str:
        return EVENT_ACTION_MAP.get(self.event_type)
```

[View source: `app/models/wtl.py`][app/models/wtl.py]

## 6. Extract and derive identifiers and attributes

The connector extracts all required identifiers and attributes from the incoming event and its nested data. Helper methods in `pb_event.py` handle extraction of IMSI, MSISDN, account ID, billing status, block status, and profiles. These methods encapsulate logic for handling missing fields, applying defaults, and validating values (such as IMSI format via regex). This separation makes the code easier to test and adapt to changes in the event schema, and ensures that all required data is available before building the WTL request.

```py title="app/services/pb_event.py" linenums="23"
def get_imsi_from_sim_info(self) -> str:
    return self.sim_info and self.sim_info.imsi
```

```py title="app/services/pb_event.py" linenums="31"
def get_account_id(self) -> Optional[str]:
    if not self.account_info:
        return None
    account_id = self.account_info.id
    return account_id.split("@msisdn")[0] if "@msisdn" in account_id else None
```

```py title="app/services/pb_event.py" linenums="37"
def get_bill_status(self) -> Optional[BillStatus]:
    return self.account_info and self.account_info.bill_status
```

```py title="app/services/pb_event.py" linenums="40"
def get_block_status(self) -> Optional[bool]:
    return self.account_info and self.account_info.blocked
```

```py title="app/services/pb_event.py" linenums="68"
def get_cs_profile(self) -> str:
    return self._get_profile("cs_profile", settings.WTL_DEFAULT_CS_PROFILE)
```

```py title="app/services/pb_event.py" linenums="26"
def validate_imsi_using_regex(self, imsi: str) -> bool:
    if settings.WTL_IMSI_REGEXP and not re.search(settings.WTL_IMSI_REGEXP, imsi):
        return False
    return True
```

[View source: `app/services/pb_event.py`][app/services/pb_event.py]

```py title="app/core/event_processor.py" linenums="56"
subscriber_status = SubscriberStatus.OPERATOR_DETERMINED_BARRING.value
if (
    not processor.get_block_status()
    and processor.get_bill_status() == BillStatus.OPEN.value
):
    subscriber_status = SubscriberStatus.SERVICE_GRANTED.value
```

[View source: `app/core/event_processor.py`][app/core/event_processor.py]

## 7. Build the unified WTL request

Once all required data is extracted and derived, the connector constructs a `UnifiedSyncRequest` object. This object aggregates all the necessary fields—IMSI, subscriber status, MSISDN list, CS and EPS profiles, and the action to perform. The use of Pydantic models ensures that the request is strictly validated before being sent, reducing the risk of malformed requests reaching the WTL API. This step keeps the business logic clean and focused on data transformation.

```py title="app/core/event_processor.py" linenums="64"
request_data = UnifiedSyncRequest(
    imsi=imsi,
    subscriber_status=subscriber_status,
    msisdn=msisdn_list,
    cs_profile=processor.get_cs_profile(),
    eps_profile=processor.get_eps_profile(),
    action=action,
)
```

[View source: `app/core/event_processor.py`][app/core/event_processor.py]

## 8. Call WTL API and map errors

The connector sends the unified request to the WTL API using an HTTP client with a configurable timeout and custom headers. The response is parsed and validated against a response model. If the WTL API indicates a failure, the connector raises a domain-specific exception, which is then mapped to an appropriate HTTP error code for the client. This separation of concerns ensures that transport errors and business errors are handled cleanly and consistently.

```py title="app/services/wtl_client.py" linenums="33"
with httpx.Client(
    timeout=settings.WTL_HTTP_REQUESTS_TIMEOUT,
    headers=self.headers,
) as client:
    response = client.post(url, json=request.model_dump(exclude_none=True))
    response.raise_for_status()

    wtl_response = WTLResponse.model_validate(response.json())

    if not wtl_response.is_successful:
        raise WTLServiceError(
            message="WTL service error",
            error=wtl_response.error or "Unknown error",
        )
```

[View source: `app/services/wtl_client.py`][app/services/wtl_client.py]

## 9. Return response

After successful processing, the endpoint returns a JSON response with a 202 Accepted status. This signals to NSPS that the event was received and processed (or queued) successfully, allowing the pipeline to continue without waiting for downstream systems. If any error occurs, the connector returns a standardized error response with the appropriate HTTP status code, making it easy for clients to handle failures.

```py title="app/core/event_processor.py" linenums="86"
return JSONResponse(
    content={"message": "Event processed successfully"},
    status_code=status.HTTP_202_ACCEPTED
)
```

[View source: `app/core/event_processor.py`][app/core/event_processor.py]

<!-- References -->

[app/main.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/main.py
[app/core/middleware.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/core/middleware.py
[app/models/events.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/models/events.py
[app/models/wtl.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/models/wtl.py
[app/services/pb_event.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/services/pb_event.py
[app/core/event_processor.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/core/event_processor.py
[app/services/wtl_client.py]: https://gitlab.portaone.com:8949/read-only/wtl_hlr_hss_connector/-/tree/main/app/services/wtl_client.py