# NSPS Connector Example (Python/FastAPI)

> **About this project**

This is a minimal Python FastAPI service that listens for POST requests from NSPS containing enriched event data. It checks the Bearer token, extracts key fields (like event type and billing status), and prints them to the console. The project is intentionally simple and serves as a template for building or testing integrations with NSPS event flows.

## Project Structure

- `main.py` — application entry point
- `requirements.txt` — dependencies
- `.env.example` — example environment variables
- `.env` — your actual environment variables (not committed)
- `Dockerfile`, `docker-compose.yml` — containerization setup
- `README.md` — this documentation

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
API_TOKEN=your-secret-token
PORT=3000
```

- `API_TOKEN` — Bearer token required for authentication (must match the token sent in requests)
- `PORT` — Port on which the server will listen (default: 3000)

## Getting Started

### Local Run

1. (Optional) Create and activate a virtual environment:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Copy `.env.example` to `.env` and set your token:
    ```sh
    cp .env.example .env
    ```
4. Start the server:
    ```sh
    python main.py
    ```
    Or for development with hot-reload:
    ```sh
    uvicorn main:app --reload --host 0.0.0.0 --port 3000
    ```

### Docker

1. Build the image:
    ```sh
    docker build -t nsps-connector .
    ```
2. Run the container:
    ```sh
    docker run --env-file .env -p 3000:3000 nsps-connector
    ```
    Or using docker-compose:
    ```sh
    docker compose up --build
    ```

## Endpoints

- `POST /process-event` — receives NSPS events, checks Bearer Token, logs `event_type` and `bill_status`

## How to Test

You can test the connector manually using curl:

```sh
curl -X POST http://localhost:3000/process-event \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "3e84c79f-ab6f-4546-8e27-0b6ab866f1f5",
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
  }
'
```

### Console Output Example

You will see something like this in the console:

```
Received event: SIM/Updated | bill status: open
```

### Example of Successful Response

```json
{
    "message": "Event accepted for processing"
}
```

### Example Error Responses

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
