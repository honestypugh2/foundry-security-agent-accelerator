# Agent 365 integration architecture

Foundry manages the agent workload; Agent 365 provides applicable agent inventory,
identity/lifecycle governance and activity integration. Azure still owns resource
configuration; Entra still owns identity enforcement. Report centrally; enforce
natively. There is no fictional unified runtime authority.

The implementation provides a read-only prerequisite report, opt-in documented
ARM field inspection, and scope/time-bound operator evidence verification.
It does not invent a registry SDK or simulate Microsoft API responses in live mode.

The documented account-level `a365LoggingEnabled` setting affects contained
projects/prompt agents; `a365Status` reports enablement/license state. Even `true`
plus `Enabled` is not actual ingestion proof. Hosted-agent telemetry has distinct
SDK and session requirements and must not be inferred from this prompt-agent lab.

Sources: [integration](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-365-integration),
[data collection](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection),
[existing agents](https://learn.microsoft.com/microsoft-agent-365/connect-existing-agents).
See [extension lab](../participant-lab/agent365-extension.md) for actual commands.
