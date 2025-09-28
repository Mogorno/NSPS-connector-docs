# NSPS Overview

The **New Service Provisioning System (NSPS)** is designed to **receive, queue, dispatch, and enrich events** from PortaBilling ESPF (External System Provisioning Framework) for delivery to [external systems][external-system]. The system is built on a **microservice architecture** and operates in the Google Cloud Platform (GCP) infrastructure.

This service is being developed as a **multi-instance solution**, where the full set of components will be deployed separately for each individual customer and/or PortaBilling environment.

## How It Works

1. PortaBilling generates an event (e.g., a subscriber upgrades their plan).
2. The built-in ESPF sends this event to NSPS via an HTTP request ([webhook][webhook]).
3. NSPS enriches the data it receives from PortaBilling by calling the PortaBilling API to fetch additional data, such as the product and access policy details.
4. The NSPS queues the event and passes it to the [connector][connector].
5. The connector communicates with the external system to apply the required changes.

## High-Level System Areas

- Service Area: Event processing components for handling ESPF events and provisioning external systems.
- Management Area: Configuration and monitoring components for system administration.
- Storage Area: Persistent storage for events, configuration, and state.

## External Network System

External Network System is any third-party platform or telecom component that must stay synchronized with PortaBilling.

These may include business tools (e.g., CRM systems, IPTV platforms) or mobile network elements (e.g., Home Subscriber Server (HSS), which manages subscriber identities, and Policy and Charging Rules Function (PCRF), which enforces policy and charging rules). Even a simple database can be treated as an external system: when employees modify data in it, PortaBilling generates an event so the administrator can manage the changes.

<!-- References -->
[webhook]: https://docs.portaone.com/docs/mr121-provisioning-via-webhooks

[external-system]: #external-network-system
[connector]: ../connector-overview.md