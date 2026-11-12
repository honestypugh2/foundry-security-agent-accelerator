# Azure-first observability with explicit open-source alternatives

## Azure path

The application uses the upstream OpenTelemetry SDK with a per-run provider,
service resource attributes and correlation on **every span**. Optional Azure
Monitor export sends spans to Application Insights, which is linked to a Log
Analytics workspace in the optional Bicep monitoring declarations.

Configure ignored `.env` only after telemetry-content, cloud and egress review:

```text
FSA_MODE=azure
FSA_EXPORT_MONITOR=true
FSA_MONITOR_CONNECTION_STRING=<your private connection string, with explicit IngestionEndpoint>
FSA_LOGS_WORKSPACE_ID=<your authorized workspace ID>
```

In addition, configure the Foundry/Search settings described in the live lab.
Cloud-specific ingestion suffix validation rejects accidental cross-cloud
export. Bicep `enableMonitoring=true` declares the workspace and Application
Insights; it does not provision them until separately authorized.

Azure Monitor uses `BatchSpanProcessor`, a bounded queue and explicit shutdown
flush. Delivery returns `SENT_NOT_INGESTION_PROOF`, `EXPORT_FAILED`, or
`NOT_ATTEMPTED`. A failed remote export fails the workflow command while keeping
the local evidence. Successful exporter return does not prove a queryable event.
Offline retry storage is disabled to avoid unreviewed content persistence.

```bash
# Real read-only query; requires workspace permissions and explicit Azure configuration:
uv run fsa observe --correlation-id <printed-correlation-id>
```

The fixed, one-hour, 50-row KQL query reads AppDependencies/AppRequests for the
specific correlation ID. It projects only timestamp, operation, span name and
success. Empty or partial results are INSUFFICIENT_EVIDENCE, not PASS.
Observed rows prove only application telemetry in that queried workspace and
window—not Agent 365, Defender, Purview, or universal trace completeness.

## Open-source paths

Default local execution uses the same upstream OpenTelemetry SDK and a JSON
ConsoleSpanExporter writing ignored local JSONL. It is fully network-free.

For an explicitly selected collector alternative outside local mode:

```text
FSA_MODE=azure
FSA_EXPORT_MONITOR=false
FSA_OTLP_ENDPOINT=http://127.0.0.1:4318/v1/traces
```

This uses stable `opentelemetry-exporter-otlp-proto-http==1.45.2`. An operator can
run an approved OpenTelemetry Collector and route to Jaeger or another compatible
backend. No collector is started, no backend availability is assumed, and no
Azure failure triggers this route automatically. Remote collectors require HTTPS;
HTTP is allowed only for explicitly configured loopback addresses.

## Dependencies and limitations

Use the stable Azure Monitor OpenTelemetry distribution (lock currently resolves
1.8.12) and `azure-monitor-query==2.0.0`. Microsoft's stable distribution currently
depends on a beta-versioned exporter; it is isolated to the optional `monitor`
extra and recorded in the lock, not represented as a separately GA exporter.
The stable upstream OTLP package similarly includes versioned experimental
transport internals. Public APIs/packages and feature maturity are distinguished.

No automatic HTTP prompt capture, request bodies, raw credentials or content
recording is enabled. Audit redaction and per-stage status replace unrestricted
SDK exception recording. For production, review sampling, retention, access,
egress, collector authentication and exporter reliability separately.

Sources: [Azure Monitor Python](https://learn.microsoft.com/python/api/overview/azure/monitor-opentelemetry-readme),
[Log Analytics SDK](https://learn.microsoft.com/python/api/overview/azure/monitor-query-readme),
[OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/).
