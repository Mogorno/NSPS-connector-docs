# Technical Specifications

## Performance and Scalability

- **Throughput Capacity**: Supports up to 10 million mobile subscribers.
- **Event Processing Time**: Processes single events within 3 seconds of receipt (excluding API response time from PortaBilling and processing time on [connector][connector] and external system side).
- **Queue Capacity**: Unlimited event buffering through cloud-based queuing (PubSub).
- **Retry Capabilities**:
    - Main subscription: ~24 hours of retries (100 attempts, 1-10 minutes delay).
    - Long Retry: Exponential backoff with increasing intervals (1h 2h 4h 8h 16h 24h max) for approximately one month in total.

## Data Handling

- **Event Storage**: Retains event history for up to 3 months.
- **Cache TTL**: Default 5 seconds with configurable values.
- **Data Consistency**: Uses event timestamps to ensure chronological integrity during processing.
- **Message Size Limit**: Typical ESPF event is ~0.2KB; typical enriched event is ~1.5KB; in complex cases enriched data may reach up to 1MB.

## Security and Authentication

- **Authentication Methods**:
    - HTTP Basic Auth for inbound webhook events.
    - Service account/identity-based authentication for inter-service communication.
    - Token-based authentication for connector interfaces.
- **Access Control**: Role-based access control for UI and management interfaces.

## Reliability and Fault Tolerance

- **Availability**: Built on cloud infrastructure with 99.9% availability SLA.
- **Error Handling**:
    - Automatic retries with exponential backoff.
    - Long replay mechanism for persistently failing events (retries for up to one month with increasing intervals).
    - Manual replay capability for persistent failures.
- **Maintenance Mode**: Ability to pause event processing during maintenance windows.
- **Monitoring**: Real-time monitoring of queue depths, processing rates, and error counts.

<!-- References -->
[connector]: ../connector-overview.md