# Agent 365 integration architecture

Foundry manages the agent workload; Agent 365 provides applicable agent inventory,
identity/lifecycle governance and activity integration. Azure still owns resource
configuration; Entra still owns identity enforcement. Report centrally; enforce
natively. There is no fictional unified runtime authority.

**Current workshop authority is read-only native evidence checks and detailed
portal/SDK guidance. Native configuration changes are excluded.** Dedicated
presentation setup in the existing private project is not native publication,
consent, RBAC, licensing or governance authorization. Application telemetry export
configuration requires separate reviewed approval, never inferred from invocation consent.

The implementation provides a read-only prerequisite report, opt-in documented
ARM field inspection, and scope/time-bound operator evidence verification.
It does not invent a registry SDK or simulate Microsoft API responses in live mode.

The documented account-level `a365LoggingEnabled` setting affects contained
projects/prompt agents; `a365Status` reports enablement/license state. Even `true`
plus `Enabled` is not actual ingestion proof. Hosted-agent telemetry has distinct
SDK and session requirements and must not be inferred from this prompt-agent lab.

## Current integration choices: native, SDK and observability

The [Agent 365 SDK overview][sdk] is explicit about integration paths:

| Route | Appropriate use | Not implied |
|---|---|---|
| Supported native platform integration | Use the platform's native route without adding the SDK | Every code-level SDK capability is available |
| Developer SDK integration | Add selected identity, governed Work IQ tooling or notification capabilities | SDK builds, hosts, orchestrates or executes the agent |
| Connected-platform registry synchronization | Import platform agents through the supported synchronization route | Runtime tools, approvals or activity ingestion validated |

Microsoft Agent Framework supplies an agent/workflow orchestration layer; the
Agent 365 SDK runs alongside the chosen runtime. It does not choose models or
execute function handlers. Notifications and particular agent-user capabilities
have additional eligibility requirements; verify those independently rather than
assuming an inventory entry supplies them. Supported platforms can appear in
inventory without a developer adding the SDK, per the [current overview][sdk].

For **new observability integrations use the separate
[Microsoft OpenTelemetry Distro][otel]**. Do not add deprecated Agent 365
observability SDK packages. The current distro guidance separates exporter
destinations and authentication routes; authorization must match the selected
route. This architecture document does not configure any of them or grant
permissions. Older Foundry pages may retain earlier hosted-SDK terminology;
consult current distro/migration guidance for a separately authorized design,
not as permission to install legacy packages.

The repository's application OpenTelemetry/Monitor evidence is independent of
native Agent 365 activity. Adding a trace exporter is not agent publication.
An exporter report is not destination ingestion, and Monitor ingestion is not
Agent 365 ingestion. The added live invocation examples require independent default-off consent for
already-configured Monitor/OTLP egress. They do not configure exporters.

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

## PRESENTATION runtime versus native capabilities

The existing no-tools **EQUIPMENT compatibility** agent/index configuration is
preserved. The independent PRESENTATION profile uses
`presentation_agent_name=contoso-policy-assistant`,
`presentation_search_index=fsa-presentation-synthetic` and a pinned
`presentation_agent_version` returned by separately authorized setup. Only NEW
dedicated agent/index creation and the approved synthetic corpus are in setup
scope; name collisions require review, not overwrite/reuse.

`foundry_security_accelerator.presentation_live` exposes workshop APIs
`review(settings)`, `setup(settings, authorized=False)`,
`run_question(settings, text, role, state_dir, authorized=False)`, and
`run_scenes(settings, state_dir, authorized=False)`, each returning a dictionary.
These are application APIs, not invented Microsoft registry/approval endpoints.
The six-scene loop is capped at three model calls per scene. At most 18 model
calls are approved across the initial verification; optional notebooks do not
each receive another allowance.

Execution is serial, with at most six proposed tool calls per scene/question;
the third/final model round uses `tool_choice=none`. The live question report
includes `audit`, `audit_head`, `audit_verified`, `trace_path`,
`trace_export_status`, `correlation_id`, `model_calls`, `citations`, `status`,
`tool_calls` and `quarantined_sections`. These are not the EQUIPMENT
`traces`/`telemetry_export` fields. The scene report returns `status`, `scenes`
and `manifest_path`, with structural per-scene checks, not model-judge scores.
Expected denials and real failures remain distinct truthful outcomes.

Read-only `azure agent-status --profile presentation` and
`agent365 ... --profile presentation` select the dedicated agent instead of
EQUIPMENT; preview opt-in remains independent. Azure-mode `audit verify` reads
the latest LIVE session, and Azure-mode `trace list` / `trace show S4` reads saved
live scene spans. These observations cannot establish native activity or security
findings.

The real model requests one of four directly attached functions:
`search_policies`, `get_policy_section`, `get_ticket_status`, or
`create_records_request`. Before execution, the client validates requested
capability/arguments and enforces policy. Search uses only the approved synthetic
corpus. The records function can queue local persistent review work; it does not
write to a remote business system.

**No Toolbox is required.** Portal-visible schemas do not mean the playground
executes the application's local handlers. Use the authorized client loop.
Microsoft's [function-calling guidance][functions] describes this separation
between model-requested calls and application execution. These functions are not
Agent 365 governed Work IQ tooling merely because they are attached to a Foundry
agent.

The shared live/local queue uses existing
`presentation_runtime.list_approvals(...)` and `approve_request(...)`.
Supplied approved execution remains **DRY_RUN only**, and role/reviewer labels are
**SYNTHETIC_ROLE_LABELS_NOT_ENTRA_OBO**. Persistence and synthetic separation of
duties are useful demonstration boundaries, not authenticated enterprise approval.
A visible native agent identity does not repair that application limitation.
The local unsafe negative control is confined to in-memory simulation and must
never become a remote attack bypass or an unsafe live mode.

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

### Read-only portal/SDK evidence sequence

1. Establish the authorized tenant/cloud/account/agent and observation window
   privately. Keep developer credential principal, agent identity, application
   correlation ID and native registry ID distinct.
2. Read offline prerequisites first. For the existing adapter's optional account
   read, explicitly opt into the documented preview operation. Do not PATCH
   `a365LoggingEnabled` or any other setting.
3. Confirm existing licensing and accepted consent with the responsible authorized
   administrator. Missing prerequisites are gaps to record, not authority to
   purchase, enroll, grant consent or assign roles.
4. Inspect existing native inventory, identity, owner and sponsor through the
   supported portal route. Creation of a Foundry version alone is not publication.
5. Observe an actual eligible correlated native event independently. The
   [Foundry integration guidance][integration] and [collection guidance][collection]
   establish why account settings, licensing/consent, publication and activity
   require separate consideration.
6. Collect private, scoped and fresh operator observations. The adapter checks
   tenant/agent match, capability completeness, duplicates and a 24-hour window;
   it does not authenticate the observer, linked evidence or remote service.
7. Review Defender/Purview only within independently authorized existing scope.
   Do not generate attacks, toggle policies, publish, block/unblock or alter
   native state to obtain evidence.

No undocumented registry SDK, automatic native approval, licensing mutation or
fictional successful response is introduced. UNKNOWN/PARTIAL remain valid evidence
gaps; a local fixture PASS cannot fill them.

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

## Verified claim references and official source repositories

Checked 2026-11-12. Claims are scoped to the cited current documentation, not
independently validated tenant behavior:

- [Agent 365 SDK overview][sdk]: native platform route without adding SDK;
  SDK identity, governed Work IQ tooling and notifications; no orchestration/
  hosting/model selection; deprecated observability warning.
- [Microsoft OpenTelemetry Distro][otel]: separate current observability surface.
- [Foundry integration][integration] and [collection][collection]: publication,
  account-level collection inheritance and licensing/consent boundaries.
- [Function calling][functions]: model requests, client executes and returns.
- [Microsoft Agent Framework source](https://github.com/microsoft/agent-framework):
  agent/workflow implementation reference.
- [Azure AI Projects SDK source](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects):
  Foundry client contracts.
- [Agent 365 Python SDK source](https://github.com/microsoft/Agent365-python):
  selected developer-integrated capabilities.
- [Microsoft OpenTelemetry Python source](https://github.com/microsoft/opentelemetry-distro-python):
  current distro implementation.

No source code is copied, no packages are installed, and no upstream example
authorizes native configuration or private data transfer.

[sdk]: https://learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-sdk?tabs=python
[otel]: https://learn.microsoft.com/en-us/microsoft-agent-365/developer/microsoft-opentelemetry
[integration]: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-365-integration
[collection]: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/configure-agent-365-data-collection
[functions]: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling
