# Testing

We recommend testing the connector in a **controlled (artificial) environment** before deploying it to production to ensure correct behavior and reliability.

!!! info "Note"
    The following list contains a minimal set of test cases that should be executed. Additional tests may be required to verify the connector’s specific event processing logic.

**1. Connector health check**

**Input:**

- Request: `GET /health`

**Response:**

- Response: `200 OK`
- Body: 
  ```json
  {}
  ```

**Expected result:**

- Confirms connector operational status.
- ES remains unchanged.
- Log records successful health check.

**2. Process valid event**

**Input:**

- Request: `POST /process-event`
- Headers: valid Bearer token
- Body: valid event

**Response:**

- Response: `202 Accepted`
- Body: 
  ```json
  {
    "message": "Event accepted for processing"
  }
  ```

**Expected result:**

- Indicates normal operation and data flow.
- ES updated as expected.
- Log records event acceptance.

**3. Reject invalid or missing token**

**Input:**

- Request: `POST /process-event`
- Headers: invalid or missing Bearer token
- Body: valid event

**Response:**

- Response: `401 Unauthorized`
- Body:
  ```json
  { 
    "message": "Invalid access token", 
    "error": "Unauthorized", 
    "type": "AUTHENTICATION_ERROR" 
  }
  ```

**Expected result:**

- Confirms authentication validation is enforced.
- ES remains unchanged.
- Log records authentication failure.

**4. Handle non-existent resource**

**Input:**

- Request: `POST /process-event`
- Headers: valid Bearer token
- Body: event referencing unknown or deleted entity

**Response:**

- Response: `404 Not Found`
- Body:
  ```json
  {
    "message": "Resource not found",
    "error": "Not found",
    "type": "VALIDATION_ERROR"
  }
  ```

**Expected result:**

- Confirms validation of referenced entities.
- ES remains unchanged.
- Log records missing resource error.

**5. Reject unsupported HTTP method**

**Input:**

- Request: `GET /process-event`
- Headers: valid Bearer token
- Body: valid event

**Response:**

- Response: `405 Method Not Allowed`
- Body:
  ```json
  {
    "message": "Method not allowed",
    "error": "Method not allowed",
    "type": "VALIDATION_ERROR"
  }
  ```

**Expected result:**

- Validates endpoint method restrictions.
- ES remains unchanged.
- Log records invalid method attempt.

**6. Validate request schema**

**Input:**

- Request: `POST /process-event`
- Headers: valid Bearer token
- Body: event with missing or malformed fields

**Response:**

- Response: `422 Unprocessable Entity`
- Body:
  ```json
  {
    "message": "Validation failed",
    "error": "Validation failed",
    "type": "VALIDATION_ERROR"
  }
  ```

**Expected result:**

- Confirms input schema validation is enforced.
- ES remains unchanged.
- Log records event validation failure.

**7. Enforce rate limits**

**Input:**

- Rapid repeated requests: `POST /process-event`
- Headers: valid Bearer token
- Body: valid event

**Response:**

- Response: `429 Too Many Requests`
- Body:
  ```json
  {
    "message": "Too many requests to API Core",
    "error": "Rate limit exceeded",
    "type": "RATE_LIMIT_ERROR"
  }
  ```

**Expected result:**

- Confirms rate limiting mechanism works correctly.
- ES remains unchanged.
- Log records rate limit violation.

**8. Handle internal server error**

**Input:**

- Forced internal exception in event handler

**Response:**

- Response: `500 Internal Server Error`
- Body:
  ```json
  {
    "message": "API Core HTTP error",
    "error": "Internal server error",
    "type": "SERVICE_ERROR"
  }
  ```

**Expected result:**

- Verifies resilience to internal failures.
- ES remains unchanged.
- Log records internal error event.

**9. Handle Core service unavailability**

**Input:**

- Simulated timeout or Core API outage

**Response:**

- Response: `503 Service Unavailable`
- Body:
  ```json
  {
    "message": "Core service is not available",
    "error": "Connection timeout",
    "type": "CONNECTION_ERROR"
  }
  ```

**Expected result:**

- Confirms correct handling of external dependency downtime.
- ES remains unchanged.
- Log records service unavailability.

**10. Graceful shutdown**

**Input:**

- Simulated service stop or restart

**Response:**

- Response: graceful stop message or status

**Expected result:**

- Verifies connector shuts down cleanly without losing in-progress tasks.
- ES remains consistent.
- Log records shutdown sequence.

## Manual API testing using `curl`

After serving the connector locally, you can send test requests to it with curl:

!!! note "Note"
    You can put event data in the `JSON` file for convinience, and refer to it in the request.

=== "bash"

    Health check:
    ```bash title="bash"
    curl -X GET "http://localhost:8000/health"
    ```

    Process event:
    ```bash title="bash"
    curl -X POST "http://localhost:8000/process-event" \
      -H "Authorization: Bearer <YOUR_API_TOKEN>" \
      -H "Content-Type: application/json" \
      -d @<PATH_TO_MOCK_EVENT_DATA.json>
    ```

=== "PowerShell"

    Health check:
    ```powershell title="powershell"
    curl -Method GET "http://localhost:8000/health"
    ```

    Process event:
    ```powershell title="powershell"
    curl -Method POST "http://localhost:8000/process-event" `
      -Headers @{ "Authorization" = "Bearer <YOUR_API_TOKEN>"; "Content-Type" = "application/json" } `
      -Body (Get-Content "<PATH_TO_MOCK_EVENT_DATA.json>" -Raw)
    ```

For test cases #7–9, consider using a mock HTTP server to simulate the external system.

**Example Python mock server**

1. Create a python script `mock_es.py`:

    ```py linenums="1" title="mock_es.py"
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class MockHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(<STATUS_CODE>)
            self.end_headers()
            self.wfile.write(b'<MESSAGE>')

    if __name__ == "__main__":
        HTTPServer(('0.0.0.0', 8081), MockHandler).serve_forever()
    ```

2. Run it with:

    ```bash title="bash"
    python3 mock_es.py
    ```

3. Update the connector configuration so that the ES URL points to `http://localhost:8081/test`

This setup allows you to simulate various ES responses (e.g., 429, 500, 503) and verify that the connector handles them correctly.

## Example mock event data

??? example "Valid event"

    ```json
    {
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
      "handler_id": "hlr-hss-nsps",
      "created_at": "2025-03-12T16:47:30.443939+00:00",
      "updated_at": "2025-03-12T16:47:36.585885+00:00",
      "status": "received"
    }
    ```

??? example "Malformed event"

    ```json
    {
      "event_id": "d2b93013-8a45-46d3-943b-5b65c8a1c5de",
      "data": {
        "event_type": "SIM/Updated"
      },
      "handler_id": "hlr-hss-nsps",
      "created_at": "2025-03-12T16:47:30.443939+00:00",
      "updated_at": "2025-03-12T16:47:36.585885+00:00",
      "status": "received"
    }
    ```