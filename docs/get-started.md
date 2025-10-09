# Get Started [![edit icon](assets\images\file-edit-outline.svg){ .icon-link }](https://gitlab.com/sonya.brnv/test/-/edit/main/docs/get-started.md)

## NSPS Preparation

Configure a **Handler** in the [NSPS][nsps] system before creating a connector.
The **Handler** is responsible for sending events to the connector server. Specify the following parameters during setup:

1. **Event Types**  
   The types of events your connector will receive. More details here: [Event Types][event-types]

2. **Required Data**  
   Additional data that [NSPS][nsps] will add to the event. More details here: [Request Body][request-body]

3. **Service URL**  
   The address of your connector where [NSPS][nsps] will send events.  
   For example: `https://my-server.com/my-event`

4. **Bearer Token**  
   For security, all requests from [NSPS][nsps] are signed with a token.  
   Your connector must verify this token in every request using the header: `Authorization: Bearer <your_token>`

After configuring the **Handler** in [NSPS][nsps], you are ready to proceed to creating your own connector.

## Creating an NSPS Connector

Before you start, we recommend reviewing the original repository:

=== "TypeScript"

    [NSPS Connector Example (TypeScript/Express)][ts-repo]

=== "Python"

    [NSPS Connector Example (Python/FastAPI)][py-repo]

!!! note "In this section you will learn how to:"

    - create a server that receives events from NSPS;
    - add a `/process-event` route to handle these events;
    - verify the Bearer Token in requests;
    - process and print the required data to the console;
    - send a response in the format expected by NSPS.

### Dependencies

This project uses third-party libraries and services required for the connector to work:

=== "TypeScript"

    ```json title="package.json"
    "dependencies": {
        "dotenv": "^17.2.3",
        "express": "^5.1.0"
    },
    "devDependencies": {
        "@types/express": "^5.0.3",
        "@types/node": "^24.6.2",
        "nodemon": "^3.1.10",
        "typescript": "^5.9.3"
    },
    ```

=== "Python"

    ```text title="requirements.txt"
    fastapi==0.118.0
    uvicorn[standard]==0.37.0
    python-dotenv==1.1.1
    ```

---

### Server Setup

First, create a server that listens on a specific port (for example, `3000`) and add a basic `/process-event` route.

> **Important!** Create a `.env` file in the project root and add the following variables:
>
> ```env title=".env"
> API_TOKEN=your_secret_token
> PORT=3000
> ```

> Replace `your_secret_token` with your own token that you will specify in the NSPS Handler.

=== "TypeScript"

    ```ts linenums="1" title="index.ts"
      import express from 'express';
      import type { Request, Response, NextFunction } from 'express';
      import dotenv from 'dotenv';

      dotenv.config();

      const app = express();
      app.use(express.json());

      const API_TOKEN = process.env.API_TOKEN || 'your-secret-token';
      const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;

      app.post('/process-event', (req: Request, res: Response) => {
          res.status(202).json({ message: 'Event accepted for processing' });
      });

      app.listen(PORT, () => {
          console.log(`Connector listening on port ${PORT}`);
      });
    ```

=== "Python"

    ```py linenums="1" title="main.py"
    import os
    from fastapi import FastAPI, Request, HTTPException, status, Depends
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from dotenv import load_dotenv

    load_dotenv()

    app = FastAPI()

    API_TOKEN = os.getenv("API_TOKEN", "your-secret-token")
    PORT = int(os.getenv("PORT", 3000))


    @app.post("/process-event")
    async def process_event(
        request: Request,
    ):
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": "Event accepted for processing"},
        )


    if __name__ == "__main__":
        import uvicorn

        uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
        print(f"Connector listening on port {PORT}")
    ```

---

### Token Verification

To ensure security, NSPS always sends the token in the **Authorization** header. Your connector must verify it before processing the event.

=== "TypeScript"

    ```ts linenums="13" hl_lines="1-12 14" title="index.ts"
    function verifyBearerToken(req: Request, res: Response, next: NextFunction) {
        const auth = req.headers['authorization'] || '';
        const token = auth.replace('Bearer ', '');
        if (!auth.toString().startsWith('Bearer ') || token !== API_TOKEN) {
            return res.status(401).json({
                message: 'Authentication failed',
                error: 'Invalid API token',
                type: 'AUTHENTICATION_ERROR',
            });
        }
        next();
    }

    app.post('/process-event', verifyBearerToken, (req: Request, res: Response) => {
        res.status(202).json({ message: 'Event accepted for processing' });
    });
    ```

=== "Python"

    ```py linenums="14" hl_lines="1 4-16 22" title="main.py"
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
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": "Event accepted for processing"},
        )
    ```

---

### Event Processing

You can extract the required data from the event body (for example, `eventType` and `billStatus`). In the example below, this data is simply printed to the console. At this stage, you can implement your own business logic: send data to an external system, save it to a database, etc.

=== "TypeScript"

    ```ts linenums="26" hl_lines="2-15" title="index.ts"
    app.post('/process-event', verifyBearerToken, (req: Request, res: Response) => {
        const { data, pb_data } = req.body;

        const eventType = data?.event_type;
        const billStatus = pb_data?.account_info?.bill_status;

        if (!eventType || !billStatus) {
            return res.status(422).json({
                message: 'Validation failed',
                error: 'Validation failed',
                type: 'VALIDATION_ERROR',
            });
        }

        console.log('Received event:', eventType, '| bill status:', billStatus);

        res.status(202).json({ message: 'Event accepted for processing' });
    });
    ```

=== "Python"

    ```py linenums="32" hl_lines="6-22" title="main.py"
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

---

### Testing

This section shows what a test request from NSPS looks like, what response the connector returns, and what will be displayed in the console.

#### 1. Example message from NSPS

Testing can be performed without NSPS by simulating a typical NSPS request.

See more about the structure in [Request Body][request-body]

??? example

    ```bash title="bash"
    curl -X POST http://localhost:8000/process-event \
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
            "i_account": 1,
            "i_customer": 6392,
            "i_product": 3774,
            "id": "79123456789@msisdn",
            "phone1": "",
            "product_name": "wtl Pay as you go",
            "time_zone_name": "Europe/Prague",
            "assigned_addons": [
              {
                "addon_effective_from": "2025-05-16T12:59:46",
                "addon_priority": 10,
                "description": "",
                "i_product": 3775,
                "i_vd_plan": 1591,
                "name": "wtl Youtube UHD"
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
            "name": "WTL integration test",
            "attributes": [
              {
                "group_name": "lte.wtl",
                "name": "cs_profile",
                "value": "cs-pp-20250319"
              },
              {
                "group_name": "lte.wtl",
                "name": "eps_profile",
                "value": "eps-pp-20250319"
              }
            ]
          }
        },
        "handler_id": "p1-nsps",
        "created_at": "2025-03-12T16:47:30.443939+00:00",
        "updated_at": "2025-03-12T16:47:36.585885+00:00",
        "status": "received"
      }'
    ```

> This example simulates a standard NSPS request and verifies that the connector processes events correctly.

#### 2. Connector response

**Connector response upon successful request processing:**

```json
{
    "message": "Event processed successfully"
}
```

**If the token is missing or invalid:**

```json
{
    "message": "Authentication failed",
    "error": "Invalid API token",
    "type": "AUTHENTICATION_ERROR"
}
```

**If the request body is invalid or required fields are missing:**

```json
{
    "message": "Validation failed",
    "error": "Validation failed",
    "type": "VALIDATION_ERROR"
}
```

#### 3. What you will see in the console

```
Received event: SIM/Updated | bill status: open
```

---

> See also the main documentation: [NSPS connector][connector]

<!-- References -->

[nsps]: NSPS/nsps-overview.md
[event-types]: implementation-specific/request-handling/event-types.md
[request-body]: implementation-specific/request-handling/request-body.md
[ts-repo]: https://github.com/Mogorno/NSPS-connector-docs/tree/main/docs/examples/typescript/simple-connector-express
[py-repo]: https://github.com/Mogorno/NSPS-connector-docs/tree/main/docs/examples/python/simple-connector-fastapi
[connector]: connector-overview.md
