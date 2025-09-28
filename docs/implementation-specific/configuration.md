# Configuration

Typically, a connector should contain parameters that are needed to connect to the external system, as well as some that are needed by the application itself. The simplest and most straightforward option is to pass environment variables.

The connector must verify all requests by checking the Bearer token. Therefore, there is a need to set this token in the connector. It is recommended to set it as an environment variable (e.g., `API_TOKEN`) and read it in the code. This way, by changing only the environment variable, you can quickly update the access token in case it is compromised.

**Requirements:**

- Configurable bearer token to access the service.
- Configurable external system credentials.