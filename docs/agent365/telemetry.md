# Agent 365 telemetry boundaries

Application OpenTelemetry -> Azure Monitor/Application Insights is implemented.
That path alone does not establish Agent 365 activity integration.

The read-only account inspection checks documented `a365LoggingEnabled` and
`a365Status` fields through explicit `2026-03-15-preview` opt-in. Enabled data
collection plus a licensed account is a prerequisite, not ingestion proof.
Prompt-agent versus hosted-agent requirements must be verified separately.

Observe an authorized synthetic interaction in the intended Agent 365 product
surface; record tenant, agent, event time, product identifier and evidence link.
Keep "requested", "enabled", "exported" and "observed" distinct.

[Microsoft collection documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection),
[application telemetry](../observability/trace-architecture.md),
[signal matrix](signal-scope-matrix.md).
