import os
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")
PORT = int(os.getenv("PORT", 3000))

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
    print(f"Connector listening on port {PORT}")
