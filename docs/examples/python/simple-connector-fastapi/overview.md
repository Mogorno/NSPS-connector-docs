# Simple Connector (Python / FastAPI)

This example is a minimal NSPS connector implemented with FastAPI. It's intended as a starting point to show how to receive events from NSPS, verify the Bearer token, extract required fields from the request body, and return the expected responses.

## What this project is

- A lightweight HTTP server that accepts POST requests from NSPS at `/process-event`.
- Demonstrates secure token-based verification (Authorization: Bearer <token>).
- Shows simple validation of incoming event payload and how to read nested fields (for example `data.event_type` and `pb_data.account_info.bill_status`).
- Meant for local testing and as a template for building production connectors.

## Technologies used

- Python 3.11+ (compatible with recent FastAPI/uvicorn releases)
- FastAPI for the web framework
- Uvicorn as ASGI server
- python-dotenv for loading environment variables from a `.env` file

Dependencies (from `requirements.txt`):

```
fastapi==0.118.0
uvicorn[standard]==0.37.0
python-dotenv==1.1.1
```

## Project layout (key files)

- `main.py` — application entrypoint that defines the FastAPI app, token verification dependency, and `/process-event` route.
- `.env.example` — example environment variables (API_TOKEN, PORT).
- `requirements.txt` — pinned Python dependencies.
- `Dockerfile`, `docker-compose.yml` — containerization files for running the example in Docker (optional).

## Code explanation

Token verification using FastAPI dependencies (HTTPBearer):

```py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
import os

API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")

bearer_scheme = HTTPBearer()


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Authentication failed",
                "error": "Invalid API token",
                "type": "AUTHENTICATION_ERROR",
            },
        )
```

Processing the event payload and simple validation:

```py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.post("/process-event")
async def process_event(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(verify_bearer_token),
):
    body = await request.json()
    data = body.get("data", {})
    pb_data = body.get("pb_data", {})
    event_type = data.get("event_type")
    bill_status = pb_data.get("account_info", {}).get("bill_status")

    if not event_type or not bill_status:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Validation failed",
                "error": "Validation failed",
                "type": "VALIDATION_ERROR",
            },
        )

    print(f"Received event: {event_type} | bill status: {bill_status}")

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": "Event accepted for processing"},
    )
```

## How to run locally

1. Copy `.env.example` to `.env` and set `API_TOKEN` and `PORT`.
2. Create a virtual environment and install requirements:

```
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

3. Run with uvicorn:

```
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

Or use the provided `Dockerfile` / `docker-compose.yml` for containerized runs.

## Notes

- This example is intentionally simple — extend it with structured logging, robust validation (Pydantic models), retries, persistence, or integration with other services as needed.
- Ensure the `API_TOKEN` used by NSPS Handler matches your connector's token.

Also see [README][readme] file

<!-- References -->

[readme]: https://github.com/Mogorno/NSPS-connector-docs/tree/main/docs/examples/python/simple-connector-fastapi
