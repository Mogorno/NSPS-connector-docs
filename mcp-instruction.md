# Create a Connector with AI

Connector can be easily created with AI help. To do this, you must provide the AI agent with the necessary documentation via an MCP server.

## Prerequisites

1. An IDE that supports MCP server integration (e.g., [Cursor][cursor], [VS Code][vs-code]).
2. Access to AI features in the IDE.

## Create a Context7 Account

1. Sign up at [Context7][context7].
2. Open the `Dashboard` and in the `Connect` section, click `Generate a new API key`.  
3. Copy and securely store your `API KEY`.

## Add an MCP Server to the IDE

=== "Cursor"

    1. Open `Settings` → `Cursor Settings` → `MCP` → `Add new global MCP server`.
    2. Paste the following configuration into `~/.cursor/mcp.json` file:

    ```json title="~/.cursor/mcp.json"
    {
      "mcpServers": {
        "context7": {
          "url": "https://mcp.context7.com/mcp",
          "headers": {
            "CONTEXT7_API_KEY": "YOUR_API_KEY"
          }
        }
      }
    }
    ```

=== "VS Code"

    1. Open `Extensions` → search for `@mcp` → `Browse MCP Servers`.
    2. Select `Context7` → `Install`.

    Alternatively, create a `.vscode/mcp.json` file in your workspace with the following content:

    ```json title=".vscode/mcp.json"
    "mcp": {
      "servers": {
        "context7": {
          "type": "http",
          "url": "https://mcp.context7.com/mcp",
          "headers": {
            "CONTEXT7_API_KEY": "YOUR_API_KEY"
          }
        }
      }
    }
    ```

## Prompt AI to Create a Connector

!!! info "Important"
    MCP server tools are available only when the AI runs in **Agent mode**.

Use the template below to instruct the AI. Replace the placeholders with details about your [ES (external system)][external-system].

!!! info "Important"
    You may skip any steps marked as "optional" — the AI agent will fill in the gaps for you. However, the more clearly you describe your ES and its requirements, the more accurately the AI will be able to generate the connector.

!!! warning "Security tip"
    Do not share actual credentials in the prompt. Pass them securely through environment variables instead.

```prompt title="Prompt template"
Create a connector between NSPS and the external system <ES name> using the context7 library https://mogorno.github.io/NSPS-connector-docs/llms.txt.

Short description: <short description of the ES and its purpose>

API base URL: <ES base>  # optional, can be provided via environment variable
API documentation: <API docs URL> # if available

Authentication & authorization:
- Method: <auth type, e.g., API key / OAuth2 / Basic>
- Token rotation / refresh: <yes / no — specify expiry, rotation period, refresh method>
- Credential scope: <list of API scopes or permissions>

Supported event types & mapping:
- <NSPS event type>
    - Required fields: <list>
    - Validation rules: <types, regex, ranges>
    - Fields mapping: <trim / pad, format date / time, convert units, etc.>
    - Target ES action: <create / update / delete, etc.>
    - Example request to the ES:
      ```http
      <HTTP method> https://<ES base>/<endpoint>
      Authorization: <auth type>
      Content-Type: <content type>
      <request body>
      ```
    - Expected success responses: <response codes and schemas>

Rate limits: # if exist
- Request limits: <max requests per sec / min, burst size>
- Rate-limit headers: <header names, e.g., X-RateLimit-Remaining>

Error handling: # optional, standard recommendations for error handling can be used
- NSPS side error handling:
    - <error / condition>:
      - Handling: <retry / skip / alert>
      - Logging context: <log message>
- ES side error handling:
    - ...

Operational & deployment notes:
- Required environment variables & examples:
    - <env variable>=<example value> (<short description>)
- Optional environment variables & default values:
    - <env variable>=<default value> (<short description>)
- Graceful shutdown instructions: <discard / store inflight requests, drain queues>
- Replay storage: <location or mechanism for failed events> # if required
- Dependency requirements: <language, packages, frameworks, external tools, runtime version> # optional
- Deployment options: <cloud platforms, e.g., GCP, AWS>

Additional requirements: # optional
- Observability & telemetry: <logs, metrics, tracing, alerts>
- Versioning: <ES API version, compatibility notes>
- Testing: <sandbox URLs, test credentials, sample test cases>
```

### Examples

```prompt title="Prompt example for the ES Google Sheets"
Create a connector between NSPS and the external system Google Sheets using the context7 library https://mogorno.github.io/NSPS-connector-docs/llms.txt.

Short description: Google Sheets is a cloud-based spreadsheet application from Google Workspace that allows reading, writing, and managing spreadsheet data through the Google Sheets API. The connector should enable synchronizing NSPS events data with Sheets documents in real time.

API base URL: https://sheets.googleapis.com/v4/spreadsheets
API documentation: https://developers.google.com/sheets/api/reference/rest

Authentication & authorization:
- Method: OAuth2 Service Account with JSON key
- Token rotation / refresh: Yes — access tokens expire after ~1 hour. Refresh tokens can be used to obtain new access tokens automatically.
- Credential scope: https://www.googleapis.com/auth/spreadsheets (read / write access)

Supported event types & mapping:
- SIM/Updated
    - Required fields:
        - created_at
        - pb_data.account_info.i_account
        - pb_data.account_info.bill_status
        - pb_data.account_info.billing_model
        - pb_data.sim_info.i_sim_card
        - pb_data.sim_info.imsi
    - Validation rules:
        - created_at — string (timestamp in RFC 3339 / ISO 8601 format with timezone offset), must represent a valid datetime
        - pb_data.account_info.bill_status — string
        - pb_data.account_info.billing_model — string
        - pb_data.account_info.i_account — integer
        - pb_data.sim_info.i_sim_card — integer
        - pb_data.sim_info.imsi — string matching regex '^[0-9]{15}$'
    - Fields mapping:
        - created_at=created_at
        - i_account=pb_data.account_info.i_account
        - billing_info="<bill_status> (<billing_model>)" (string)
        - i_sim_card=pb_data.sim_info.i_sim_card
        - imsi=pb_data.sim_info.imsi
    - Target ES action: Append a new row to the target Google Sheet in the specified column range with the following data (in order): created_at, i_account, billing_info, i_sim_card, imsi.
    - Example request to the ES:
      ```http
      POST https://sheets.googleapis.com/v4/spreadsheets/<SPREADSHEET_ID>/values/<SHEET_NAME>!<RANGE>:append?valueInputOption=USER_ENTERED
      Authorization: Bearer <ACCESS_TOKEN>
      Content-Type: application/json
      {
        "values": [
          [
            "2025-10-04T21:48:30.443939+00:00",
            123,
            "open (credit_account)",
            4567,
            "310150123456789"
          ]
        ]
      }
      ```
    - Expected success responses: 200 OK — response body contains updatedRange, updatedRows, updatedColumns.

Rate limits:
- Request limits: ~100 requests per 100 seconds per user (Google Sheets API default).
- Rate-limit headers:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining (unofficial — may not be always present)

Error handling:
- NSPS side error handling:
    - Unsupported event type
        - Handling: skip
        - Logging context: "Unsupported event type: <event_type>."
    - Other errors:
      - Standad responses and log messages.
- ES side error handling:
    - 401 Unauthorized
        - Handling: refresh OAuth token, retry once
        - Logging context: "Invalid access token."
    - 403 Rate Limit Exceeded
        - Handling: exponential backoff starting at 5s
        - Logging context: "Rate Limit Exceeded."
    - 404 Not Found
        - Handling: skip
        - Logging context: "Resource not found: <details>."
    - 500 / 503 Server Error
        - Handling: retry with delay (up to 3 times)
        - Logging context: "Server Error: <details>."
    - default:
        - Handling: alert
        - Logging context: "Unexpected ES error: <details>."

Operational & deployment notes:
- Required environment variables & examples:
    - API_TOKEN="secure-random-token" (Bearer token for incoming request authentication)
    - GOOGLE_CREDENTIALS_PATH="./credentials.json" (path to Google service account JSON file)
    - SPREADSHEET_ID="1t7_rgkDOpGsFrdZMZlSeQoa1nzghPk6rc_lBxfyhV0k" (Google Spreadsheet ID)
    - SHEET_NAME="Sheet1" (target sheet name)
    - RANGE="A:E" (column range for data insertion)
- Optional environment variables & default values:
    - GOOGLE_HTTP_REQUESTS_TIMEOUT=30.0 (HTTP timeout for Google API calls)
    - RETRY_COUNT=3 (retry count)
    - LOG_LEVEL="INFO" (logging level (DEBUG, INFO, WARNING, ERROR))
- Graceful shutdown instructions: Flush queue.
- Replay storage: Inmemory buffer (non-persistent).
- Dependency requirements:
    - Language: Python ≥3.10
    - Packages: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client
    - Frameworks: FastAPI

Additional requirements:
- Observability & telemetry:
    - Logging: structured JSON logging for all API requests.
    - Metrics: sheets_api_errors_total.
- Testing:
    - Sandbox: use a test Google service account with an empty spreadsheet (credentials are passed at runtime).
    - Test cases: 
        - update a known range and verify cell values
        - test handling possible errors from NSPS side
```

```prompt title="Prompt example for the ES WTL HLR/HSS"
Create a connector between NSPS and the external system WTL HLR/HSS using the context7 library https://mogorno.github.io/NSPS-connector-docs/llms.txt.

Short description: WTL HLR/HSS provides subscriber provisioning and status management functions within the mobile core network.

Authentication & authorization:
- Method: Bearer token
- Token rotation / refresh: No.

Supported event types & mapping:
- SIM/Updated
    - Required fields:
        - pb_data.sim_info.imsi
    - Validation rules:
        - pb_data.sim_info.imsi — string matching regex '^[0-9]{15}$'
    - Fields mapping:
        - imsi=pb_data.sim_info.imsi (string)
        - subscriber_status (string)
            - "operatorDeterminedBarring", if pb_data.account_info.blocked=="Y" OR pb_data.account_info.bill_status!="O" (Open)
            - "serviceGranted", if pb_data.account_info.blocked=="N" AND pb_data.account_info.bill_status=="O" (Open)
        - msisdn[] (array of string)
            1. extract MSISDN from pb_data.account_info.id (with removing @msisdn suffix)
            2. check pb_data.account_info.bill_status:
                - if =="I" (Inactive), use an empty list to avoid number provisioning / use for inactive (work in progress) account
                - if =="O" (Open), use the extracted MSISDN
                - if =="C" (Closed), use an empty list to release the used number
        - cs_profile=pb_data.access_policy_info.attributes["name"=="cs_profile"].values[0] or default value if not specified
        - eps_profile=pb_data.access_policy_info.attributes["name"=="eps_profile"].values[0] or default value if not specified
    - Target ES action: Update.
    - Example request to the ES:
      ```http
      POST https://<ES base>/wtl/hlr/v1/prov
      Authorization: Bearer <ACCESS_TOKEN>
      Content-Type: application/json
      {
        "imsi": "250991234567890",
        "subscriber_status": "SERVICE_GRANTED",
        "msisdn": ["79123456789"],
        "cs_profile": "cs-pp",
        "eps_profile": "eps-pp"
      }
      ```
    - Expected success responses: 200 OK — response body contains only message.

Error handling:
- NSPS-side error handling:
    - Validation error
      - Handling: raise HTTPException 422 Unprocessable Entity
      - Logging context: "Validation error: <error response>"
    - Other errors:
      - Standad responses and log messages.
- ES-side error handling:
    - Standard responses and log messages.

Operational & deployment notes:
- Required environment variables & examples:
    - API_TOKEN="secure-random-token" (Bearer token for incoming request authentication)
    - WTL_API_URL="http://wtl-api:3001/wtl/hlr/v1" (base URL of WTL HSS service)
    - WTL_API_TOKEN="wtl-token" (authentication token for WTL HSS API)
- Optional environment variables & default values:
    - LOG_LEVEL="INFO" (logging level (DEBUG, INFO, WARNING, ERROR))
    - WTL_DEFAULT_CS_PROFILE="cs-barred" (default CS profile if not specified in event)
    - WTL_DEFAULT_EPS_PROFILE="ps-barred" (default EPS profile if not specified in event)
- Deployment options: GCP (Cloud Run), AWS (App Runner).
```

<!-- References -->
[cursor]: https://cursor.com/download
[vs-code]: https://code.visualstudio.com/download
[context7]: https://context7.com/

[external-system]: NSPS/nsps-overview.md#external-network-system