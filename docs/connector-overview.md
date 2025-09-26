# Connector Overview

Connectors are specialized **adapter microservices** that **translate events** from the [NSPS][nsps] system into **format-specific requests** required by external network systems. Each external system integration requires a dedicated connector implementation.

## Key Responsibilities

- Receiving events from NSPS.
- Data transformation and mapping from NSPS event format to external system format.
- Authentication with external systems.
- Error handling and status reporting.
- Logging of interactions with external systems.

<!-- References -->
[nsps]: NSPS/nsps-overview.md