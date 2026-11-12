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

## Prerequisites and identity

Before any service exercise, independently confirm the intended tenant/cloud,
eligible prompt-agent type, current license/consent, owner/sponsor, supported
connection route, least-privilege access and approved telemetry retention.
Check Defender/Purview requirements separately if included.

DefaultAzureCredential authenticates an SDK caller. The tenant-bound claim guard
does not independently validate JWT signatures or create an agent identity.
Production caller-to-entitlement authentication and independent authenticated
human approval are not supplied by synthetic lab roles.
Use narrow project/workload, Search data-reader, Content Safety and Logs query
permissions; do not grant tenant-wide administrator access to make a lab pass.
Identity, role and consent changes need separate authorization.

## Publication and lifecycle authority

Creating a pinned Foundry version is not Agent 365 publication. Use the current
supported, independently authorized connection workflow; this adapter does not
publish/register agents or invent registry APIs. Retain the actual entry, agent,
owner/sponsor, connection state and observation time in approved private storage.
A portal screenshot is operator evidence, not independent API validation.

Ownership, sponsorship, inventory review and lifecycle controls belong to the
applicable native governance surfaces. A registry entry or owner label cannot
authorize a business write. Application approval binds exact proposal, subject,
scope and expiration before a DRY_RUN receipt. Review abandoned agents, access
and incidents with administrators; no automatic remediation is enabled.

## Interpreting evidence

| Evidence label | What it does and does not establish |
|---|---|
| UNKNOWN / VERIFICATION_REQUIRED | Capability has not been established; local mode performs no cloud read |
| READ_ONLY_VERIFICATION | Scoped resource-setting read, not registry/activity validation |
| MANUAL_PORTAL_STEP | Independently inspect registry, identity, owner/sponsor or activity |
| OPERATOR_ATTESTATION | Checks configured tenant/agent scope, completeness and 24-hour freshness; does not authenticate the evidence link |
| BLOCKED_BY_PREVIEW | Required explicit preview opt-in absent; not proof of missing platform entitlement |
| BLOCKED_BY_LICENSE / PERMISSION / CLOUD_SUPPORT | Use only for an actually established, scoped blocker; do not infer causes |
| NOT_IMPLEMENTED | No automated native connector or mutation exists for that operation |

An attestation PASS is not automated service validation or Microsoft
certification. Keep requested, enabled, exported and observed distinct.
The explicit `2026-03-15-preview` account-setting read remains opt-in.
Observe an authorized synthetic interaction in the intended product and record
actual scope/time privately; application OTel alone is not Agent 365 activity.
Hosted-agent requirements and sovereign-cloud availability are separate checks.

## Defender and Purview are independent observation planes

For Defender, distinguish resource posture from agent runtime findings. Verify
workload, enabled policy, license, correlation and observation window. Event
visibility, alert generation, incident correlation and enforced action are not
equivalent. A blocked application request does not guarantee an alert.

For Purview, verify the supported data path, classification/audit/DLP policy,
license and cloud. Application redaction and synthetic classification are not
enterprise DLP. A registry entry, span or model score is not Purview evidence.
No native alerts, connectors, consent or policy changes are fabricated.
Retain absent observations as UNKNOWN/VERIFICATION_REQUIRED and use the separate
local lab. See the [signal-scope matrix](signal-scope-matrix.md).

## Troubleshooting without broadening access

| Observation | Safe response |
|---|---|
| Missing preview opt-in | Review documentation and authorize only the required account read |
| Service reports NotLicensed | Resolve with the administrator; never relabel PASS |
| Enabled logging but no activity | Review eligible type/route, consent and window; retain missing-ingestion status |
| Registry absent | Workload creation is not publication; verify the supported connection route |
| Expired/wrong-scope observation | Collect fresh scoped evidence, not unrelated screenshots |
| Defender/Purview silent | Verify supported native scope/policy; no universal alert guarantee |
| Permission error | Request least-privilege review; do not automatically change roles or consent |

Keep tokens, configuration, identifiers and private captures out of public issues.
Use the [participant extension](../participant-lab/agent365-extension.md) for the
guided read-only exercise and the
[cloud guide](../clouds/commercial-vs-government.md) for availability boundaries.
