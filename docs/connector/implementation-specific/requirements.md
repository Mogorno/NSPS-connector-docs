# Requirements

- Authentication of all requests to the connector using a Bearer token.
- Event payload schema parsing.
- Handling specific [events][events] (e.g., SIM activated, Plan changed, etc.).
- Configurable settings for [External API server][external-api-server]:
    - API base URL with optional base path.
    - API access credentials (depends on the system implementation. This can be either Basic Auth, Bearer Auth with a static token, or support for example JWT. The connector should work with access_tokens and refresh_tokens if the system requires it).
- Response codes:
    - 2XX for a successfully processed event (with optional JSON response body).
    - 4XX and 5XX codes for unsuccessfully processed events (with human-readable error explanation in response JSON body).

An example is available here - [WTL HLR/HSS Connector][wtl-hlr/hss-connector].

The connector should provide 2 methods:

1. **GET health endpoint** is needed to check the availability of the connector itself (this method should return just 200 OK with some optional response body).
2. **POST method** is used by the NSPS system as a destination. The URL may or may not contain a path (options such as `https://connector.com`, `https://connector.com/api/events` are OK).

You can view or download an example of the OpenAPI specification below.

[![OpenAPI.json](../assets/images/placeholder-small-file.png)][openapi.json]

[Click here to view/download OpenAPI spec][openapi-spec]

<!-- <details>
  <summary>Click here to expand OpenAPI spec ...</summary>

```json
{% include_relative assets/OpenAPI.json %}
```
</details>  -->
