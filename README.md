# Introducing NSPS Connector

The **Network Service Provisioning System (NSPS)** is a component of PortaBilling that delivers real-time event notifications about changes in customer accounts, services, SIM cards, balances, and more.  
It allows you to integrate PortaBilling with external systems (e.g., HLR/HSS, PCRF, CRMs, or custom applications).

Before creating an NSPS Connector, you need to configure a **handler** in PortaBilling.  
A handler defines:

- Which events should be sent from NSPS
- The destination (Connector URL)
- Security parameters (authentication, headers)

➡️ See [PortaBilling Release Notes MR123](https://docs.portaone.com/docs/mr123-what-is-new) for details about NSPS handlers.

---

## What is the NSPS Connector?

The **NSPS Connector** acts as an **adapter** between NSPS and your external system:

- **Receives events**: NSPS sends enriched JSON event objects (e.g., `SIM/Updated`, `Account/Modified`).
- **Processes data**: The Connector transforms the event and passes it to the external system (API, database, or service).
- **Handles responses**: It expects a response indicating **success** or **failure** of the request.
- **Provides reliability**: In case of errors, failed events can be retried or logged for troubleshooting.

---

## Key Benefits

- Standardized interface between PortaBilling and external platforms
- Flexible integration with multiple systems
- Clear logging and monitoring of event delivery
- Simplifies building custom business logic around PortaBilling events

---

## Next Steps

1. Configure an NSPS handler in PortaBilling.
2. Deploy the NSPS Connector (Docker container, Cloud Run, AWS App Runner, etc.).
3. Test event delivery in a staging environment before connecting production systems.
