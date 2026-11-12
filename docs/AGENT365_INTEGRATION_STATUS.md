# Agent 365 integration status

Current source-level status, not live tenant certification. No Azure read or
mutation was performed during session-day alignment.

| Capability | Status | Evidence / limitation |
|---|---|---|
| Prerequisite inventory | IMPLEMENTED | Existing package returns unresolved checks |
| Preview Foundry account settings | READ_ONLY_VERIFICATION | Explicit preview opt-in; settings do not prove ingestion |
| Preview opt-in absent in Azure mode | BLOCKED_BY_PREVIEW | Explicit opt-in required; not proof platform entitlement is missing |
| Service explicitly reports NotLicensed | BLOCKED_BY_LICENSE | Only use after an actual scoped result, not inferred from missing data |
| Current permission denied | BLOCKED_BY_PERMISSION | Record only after actual authorized observation |
| Unsupported selected cloud/workload | BLOCKED_BY_CLOUD_SUPPORT | Requires independent current product evidence |
| Registry, owner, sponsor, activity inspection | MANUAL_PORTAL_STEP | No automated registry/activity query |
| Supplied observations | OPERATOR_ATTESTATION | Scope/freshness checks; no authentication of evidence reference |
| Foundry availability read | READ_ONLY_VERIFICATION | Different from registry or activity |
| Auto publish/register/consent/native connectors | NOT_IMPLEMENTED | No invented APIs or synthetic platform signals |
| Current actual tenant status | VERIFICATION_REQUIRED | No live observations made in this alignment |

Existing command outcome values remain compatible; additive `integration_status`
fields clarify evidence type. A fully populated, fresh attestation can yield PASS
but is never automated service validation. Logging enabled is not an ingested
event. Foundry invocation, Agent 365 registry, native activity, Defender and
Purview require separate observations.

Supported workload here: prompt agent, no remote tools. Hosted-agent telemetry
and Government-cloud parity are not claimed. Licensing, consent, admin roles,
identity/blueprint, owner/sponsor, residency and current preview/cloud support
must be checked by the responsible administrator. Core Azure lab remains
independent of Agent 365 licensing.
