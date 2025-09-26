# Request Headers

NSPS sends the following headers to the connector used for tracing and debugging:

- [x-b3-traceid][x-b3-traceid]
- [x-request-id][x-request-id]

The connector should process them and add them to all log messages related to the processing of a specific request. If the headers were not delivered, the connector should generate unique values (for example, use UUID-compatible format).
