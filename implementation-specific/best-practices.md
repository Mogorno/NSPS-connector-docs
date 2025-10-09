# Best Practices

This section gathers practical, actionable guidance for building reliable, secure, and maintainable [NSPS connectors][connector]. It focuses on patterns that matter most in production: authentication and security, input validation, error handling, response and event processing.

Each best practice includes why it matters, a short step-by-step implementation guide, and concise examples in `TypeScript` (`Express`) and `Python` (`FastAPI`), adapted from the example connectors in this repository.

Following these practices ensures your connector:

- Authenticates all incoming requests using the NSPS Bearer token.
- Validates incoming events to prevent processing invalid or malformed data.
- Responds to every event, both on success and error, to maintain proper acknowledgment and a complete audit trail in NSPS.
- Uses consistent error formats for predictable handling by NSPS.

## Authorization

The [NSPS Connector][connector] uses a Bearer Token to authenticate incoming requests from the [NSPS][nsps] platform.
This token is a static secret key, registered and configured in NSPS.
Every message sent from NSPS to the Connector is signed with this token, and the Connector must validate it before processing the request.

### 1. Using the Bearer Token

**Header format:**

```
Authorization: Bearer <YOUR_API_TOKEN>
```

Each incoming request from NSPS must include this header to be accepted by the Connector.

### 2. Token Verification

=== "TypeScript"

    ```typescript
    import { Request, Response, NextFunction } from 'express';
    import { settings } from './core/config';

    export function verifyToken(req: Request, res: Response, next: NextFunction) {
        const authHeader = req.headers.authorization;
        const token = authHeader?.startsWith('Bearer ') ? authHeader.split(' ')[1] : null;

        if (!token || token !== settings.API_TOKEN) {
            return res
                .status(401)
                .set('WWW-Authenticate', 'Bearer')
                .json({
                    message: 'Invalid access token',
                    error: 'Unauthorized',
                    type: 'AUTHENTICATION_ERROR',
                });
        }

        next();
    }
    ```

=== "Python"

    ```python title="verify_token.py"
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from .core.config import settings

    security = HTTPBearer()

    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify the Bearer token provided by NSPS"""
        if credentials.credentials != settings.API_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials
    ```

How it works:

- Extracts the Bearer token from the request header.

- Compares it with the configured value in `settings.API_TOKEN`.

- Raises an `HTTP 401 error` if the token does not match.

### 3. Secure Token Storage

#### Recommended storage options:

##### 1. Environment file (`.env`)

Store the token as an environment variable in your deployment environment or in a `.env` file duringlocal development:

```env title=".env"
API_TOKEN=your_secret_token_here
```

Best practices for environment variables:

- Add `.env` files to `.gitignore` so they are not committed to version control.
- Use different tokens for development, staging, and production environments.
- Keep `.env` files outside of your code repository if possible.

##### 2. Secrets Store or Vault

In production environments, use a secure secret management system instead of plain `.env` files:

- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Google Secret Manager

#### Load values ​​via the configuration system:

=== "TypeScript"

    ```typescript title="settings.ts"
    import { config as loadEnv } from 'dotenv';
    import { z } from 'zod';

    loadEnv();

    const EnvSchema = z.object({
        API_TOKEN: z.string().min(1, 'API_TOKEN is required'),
    });

    export const settings = EnvSchema.parse(process.env);
    ```

=== "Python"

    ```py title="settings.py"
    from pydantic import BaseSettings

    class Settings(BaseSettings):
        API_TOKEN: str

        class Config:
            env_file = ".env"

    settings = Settings()
    ```

This ensures your app automatically reads variables from `.env` or from environment configuration (e.g., Docker, Kubernetes, or CI/CD).

### 4. Unauthorized Access Response

If the provided token is invalid or missing, the Connector must return an `HTTP 401 Unauthorized` response. The response must be formatted in accordance with [ErrorResponse][error-responce]

Response example:

```json title="response.json"
{
    "message": "Invalid access token",
    "error": "Unauthorized",
    "type": "AUTHENTICATION_ERROR"
}
```

## Input Validation

Before processing, each NSPS event must be validated to ensure it matches the expected schema.
Validation guarantees data integrity, prevents processing of incomplete payloads, and protects the connector from runtime errors.

### 1. Why Input Validation Matters

- Ensures that only well-formed events are processed.
- Prevents null or malformed fields from causing downstream issues.
- Enables predictable, auditable, and safe event handling.

??? example "Example request:"

    ```json
    {
        "event_id": "3e84c79f-ab6f-4546-8e27-0b6ab866f1fb",
        "data": {
            "event_type": "SIM/Updated"
        },
        "pb_data": {
            "sim_info": {
            "imsi": "001010000020349"
            }
        }
    }
    ```

### 2. Validation Example

=== "TypeScript"

    ```ts title="index.ts"
    import express, { Request, Response } from 'express';
    import { z, ZodError } from 'zod';

    // ...

    // --- Zod schemas ---
    const SimInfoSchema = z.object({
        imsi: z
            .string()
            .regex(/^[0-9]{15}$/, 'IMSI must contain exactly 15 digits')
            .optional(),
    });

    const PBDataSchema = z.object({
        sim_info: SimInfoSchema,
    });

    const EventDataSchema = z.object({
        event_type: z.string(),
    });

    const EventSchema = z.object({
        event_id: z.string(),
        data: EventDataSchema,
        pb_data: PBDataSchema,
    });

    app.post('/process-event', verifyBearerToken, (req: Request, res: Response) => {
        try {
            const event = EventSchema.parse(req.body);
            // Validation passed, process the event

            // ...
        } catch (e) {
            if (e instanceof ZodError) {
                return res.status(422).json({
                    message: 'Validation failed',
                    error: 'Validation failed',
                    type: 'VALIDATION_ERROR',
                    details: e.errors,
                });
            }

            // ...
        }
    });
    ```

=== "Python"

    ```python
    from fastapi import FastAPI, HTTPException, status
    from pydantic import BaseModel, constr, ValidationError

    # ...

    class SimInfo(BaseModel):
        imsi: constr(regex=r'^[0-9]{15}$') | None = None

    class PBData(BaseModel):
        sim_info: SimInfo

    class EventData(BaseModel):
        event_type: str

    class Event(BaseModel):
        event_id: str
        data: EventData
        pb_data: PBData

    @app.post(
        '/process-event',
        # ...
        responses={
            # ...
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
            }
        },
    )
    async def process_event(event: Event, token: str = Depends(verify_bearer_token)):
        try:
            # Pydantic will validate types and regex before this code runs
        except ValidationError as e:
            error_response = {"errors": e.errors()}
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_response
            )
    ```

> Validation should be explicit for fields that drive routing or external API calls (IMSI, action types, resource IDs). Keep validation rules in small reusable modules so they can be unit-tested.

### 3. Validation Failure Response

If the payload does not pass validation, the connector must respond with `HTTP 422 Unprocessable` Entity and include validation details. [ErrorResponse][error-responce]

```json
{
    "message": "Validation failed",
    "error": "Validation failed",
    "type": "VALIDATION_ERROR"
}
```

## Sending Responses to NSPS

A recommended best practice when implementing the NSPS Connector is to always send a response back to NSPS after processing each event, regardless of whether the processing was successful or resulted in an error. This ensures that:

- Event acknowledgment: NSPS knows the event has been received and processed.

- Audit trail completeness: All responses, including success and error messages, are stored in the Event History database, providing a complete audit trail accessible via the Management UI.

- Error visibility: Sending detailed error responses helps NSPS track issues and aids in debugging and programmatic handling.

Success response example:

```json title="202 Accepted: Event accepted for processing"
{
    "message": "Event accepted for processing"
}
```

Error response example:

```json title="500 Internal Server Error: Processing error"
{
    "message": "Error processing event",
    "error": "External system connection failed",
    "type": "CONNECTION_ERROR"
}
```

More info here [Error Response Structure][error-responce].

By consistently responding to every NSPS event, your connector provides reliable feedback, maintains data integrity, and ensures that NSPS can correctly log and analyze all processed events.

<!-- References -->

[error-responce]: error-handling.md#error-response-structure
[nsps]: ../NSPS/nsps-overview.md
[connector]: ../connector-overview.md
