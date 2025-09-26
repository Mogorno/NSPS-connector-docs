# Logging

Logging is an important part that allows debugging when necessary.

**Requirements:**

- Logs should be written in JSON format (for search integration).
- Log `x-b3-traceid` header to `request_id` field.
- Log `x-request-id` header to `unique_id` field.

Logging these headers allows you to track all the events that occur with the event from its very beginning — entering the NSPS.
