# Overview

The **New Service Provisioning System (NSPS)** is designed to **receive, queue, dispatch, and enrich events** from PortaBilling ESPF (External System Provisioning Framework) for delivery to external systems (HLR, PCRF, etc.). The system is built on a **microservice architecture** and operates in the Google Cloud Platform (GCP) infrastructure.

This service is being developed as a **multi-instance solution**, where the full set of components will be deployed separately for each individual customer and/or PortaBilling environment. This approach enables deployments in different geographic regions, closer to the customer's infrastructure, in order to minimize network latency and ensure optimal performance.

## How it works

1. PortaBilling generates an event (e.g., a subscriber upgrades their plan).
2. The built-in External system provisioning framework (ESPF) sends this event to NSPS via an HTTP request (webhook).
> **Note:**
>
> NSPS supports both ESPF event versions v1 and v2.
3. NSPS enriches the data it receives from PortaBilling by calling the PortaBilling API to fetch additional data, such as the product and access policy details.
> **Note:**
>
> NSPS caches this additional data to reduce API load.
4. The NSPS queues the event and passes it to the connector.
> **Note:**
>
> NSPS uses separate event queues per connector.
5. The [connector][connector] communicates with the external system (PCRF) to apply the required changes.

## High-level system areas

- Service Area: Event processing components for handling ESPF events and provisioning external systems.
- Management Area: Configuration and monitoring components for system administration.
- Storage Area: Persistent storage for events, configuration, and state.

<!-- References -->
[connector]: ../connector/overview.md