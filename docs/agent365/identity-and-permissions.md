# Identity and permissions

`DefaultAzureCredential` authenticates a caller to supported SDK endpoints.
The tenant-bound wrapper requests the configured tenant and rejects conflicting
token tenant claims. That claim guard is not independent JWT signature validation,
and does not create an Agent 365 agent identity, sponsor or owner.

Use narrowly scoped project/workload, Search data-reader, Content Safety user
and Log Analytics query roles appropriate to each native service. Do not assign
tenant-wide administrators to make a demonstration work. Exact role assignments,
principal identifiers and consent changes require separate authorization.

Current code does not perform role assignment, identity creation or consent.
An authenticated production request-to-entitlement adapter and authenticated
independent human approver remain operator implementation requirements.
Local subjects/entitlements are synthetic trusted test inputs, not production
authentication. [Microsoft identity concepts](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity).
