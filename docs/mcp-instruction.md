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

!!! note "Note"
    MCP server tools are available only when the AI runs in **Agent mode**.

Use the template below to instruct the AI. Replace the placeholders with details about your [ES (external system)][external-system].

!!! warning "Security tip"
    Do not share actual credentials in the prompt. Pass them securely through environment variables instead.

```prompt title="Prompt template"
Create a connector between NSPS and the external system <ES name> using the context7 library https://mogorno.github.io/NSPS-connector-docs/llms.txt.

Short description: <Short description of the ES>
API URL: <ES API URL>  # (optional, can also be provided via environment variable)

Authentication:
- Method: <auth type, e.g., API key / OAuth2 / Basic>
- Details: <auth field names, headers, tokens, etc.>

Supported event types:
- <event type>
  - handler ID: <handler ID>  # optional, if multiple handlers exist
  - required fields: <required fields>
  - NSPS → ES mapping action: <ES action>
  - Example payload:
    ```json
    {
      "<field1>": "<value>",
      "<field2>": "<value>"
    }
    ```

Additional details about the ES:
- Rate limits: <info>
- Error handling: <info>
- Special transformations: <info>
```

<!-- References -->
[cursor]: https://cursor.com/download
[vs-code]: https://code.visualstudio.com/download
[context7]: https://context7.com/

[external-system]: NSPS/nsps-overview.md#external-network-system