# Error Handling

Proper error handling ensures that NSPS connectors provide clear feedback for every event, maintain a complete audit trail, and allow programmatic handling of failures.

- Errors should be logged.
- Each error response must contain a JSON body with an explanation of the reason for the error.

## Error Response Structure

All error responses must follow the `ErrorResponse` schema:

```json
{
    "message": "Detailed description of the error",
    "error": "Specific failure reason",
    "type": "ERROR_TYPE"
}
```

**Error Response Fields:**

- `message`: General description of the operation result (used in successful responses).
- `error`: Detailed error description, indicates failure processing results.
- `type`: Error type for programmatic handling. Example:

```
"VALIDATION_ERROR"
"AUTHENTICATION_ERROR"
"SERVICE_ERROR"
"CONNECTION_ERROR"
"RATE_LIMIT_ERROR"
"INTERNAL_ERROR"
```

## Standard Responses Examples

All response codes, messages, and error details are stored in the Event History database and are available for analysis via the Management UI. This provides a complete audit trail of all events processed by the system.

**202 Accepted** – Event accepted for processing:

```json
{
    "message": "Event accepted for processing"
}
```

**401 Unauthorized** – Invalid access token:

```json
{
    "message": "Invalid access token",
    "error": "Unauthorized",
    "type": "AUTHENTICATION_ERROR"
}
```

**404 Not Found** – Resource not found:

```json
{
    "message": "Resource not found",
    "error": "Not found",
    "type": "VALIDATION_ERROR"
}
```

**405 Method Not Allowed** – HTTP method not supported:

```json
{
    "message": "Method not allowed",
    "error": "Method not allowed",
    "type": "VALIDATION_ERROR"
}
```

**422 Unprocessable Entity** – Validation failed:

```json
{
    "message": "Validation failed",
    "error": "Validation failed",
    "type": "VALIDATION_ERROR"
}
```

**429 Too Many Requests** – Rate limit exceeded:

```json
{
    "message": "Too many requests to API Core",
    "error": "Rate limit exceeded",
    "type": "RATE_LIMIT_ERROR"
}
```

**500 Internal Server Error** – API or service error:

```json
{
    "message": "API Core HTTP error",
    "error": "Internal server error",
    "type": "SERVICE_ERROR"
}
```

**503 Service Unavailable** – Core service not available:

```json
{
    "message": "Core service is not available",
    "error": "Connection timeout",
    "type": "CONNECTION_ERROR"
}
```
