# Workflow

1. Accept HTTP request to `POST /process-event` with Bearer auth.
2. Set request context (trace IDs) and JSON logging via middleware.
3. Validate payload against the `Event` schema (includes `data` and optional `pb_data`).
4. Determine provisioning action from `event_type`.
5. Extract required identifiers and attributes from `pb_data`:
    - IMSI (required), MSISDN (from `account_info.id` when `bill_status == open`)
    - Subscriber status derived from `blocked` and `bill_status`
    - Profiles (`cs_profile`, `eps_profile`) from access policy or defaults
    - Optional IMSI regex validation
6. Build a unified request for the WTL API.
7. Call the external WTL API with retry-safe HTTP client and map errors to typed responses.
8. Return 202 on success (accepted/processed) or a standardized JSON error.
