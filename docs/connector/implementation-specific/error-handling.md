# Error Handling

- Errors should be logged.
- Each error response must contain a JSON body with an explanation of the reason for the error.

**Error Response Fields:**

- `message`: General description of the operation result (used in successful responses).
- `error`: Detailed error description, indicates failure processing results.
- `type`: Error type for programmatic handling (e.g., "CONNECTION_ERROR", "AUTHENTICATION_ERROR", "VALIDATION_ERROR").
