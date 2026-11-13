# Optional Agent 365 extension

**Confirmed scope:** read-only native evidence checks and detailed portal/SDK
guidance; **exclude native configuration changes**. Permission to inspect is not
permission to remediate. No publishing, tenant consent, RBAC, license assignment,
native logging or lifecycle changes are authorized by this exercise.

Core Foundry execution does not require Agent 365 licensing.
Preferred guide: [05 extension notebook](../../notebooks/05_agent365_extension.ipynb).
For a complete local request/review/approval/publication exercise, use
[Lab 07](request-approval-publish.md) and
[its notebook](../../notebooks/07_agent365_request_approval_publish.ipynb).
It demonstrates local synthetic decisions, not a native publishing connector;
the accompanying template/Requests portal checklist remains read-only.
Expected duration 20 minutes plus any platform sync; L300-L400. Complete
[setup](../../notebooks/00_environment_setup.ipynb) first. Bash and PowerShell:
`uv sync --frozen --all-extras --dev`. The executable/module entry points
are equivalent: `uv run python -m fsa agent365 preflight`.
Use an explicitly configured private `FSA_MODE=azure` for authorized nested
Agent 365 status reads; the top-level global mode is not forwarded to this
subparser. No notebook or command automatically changes consent/governance.
See the [integration guide](../agent365/integration-architecture.md#interpreting-evidence) for evidence labels,
[troubleshooting](troubleshooting.md), and [cleanup](cleanup.md).

Read [the integration source][integration] and [collection prerequisites][collection].
Confirm current SKU, tenant consent and administrator role requirements with
your tenant administrator; do not change licensing or consent from the lab.

## Choose the integration path before choosing an SDK

The current [Agent 365 SDK overview][sdk] distinguishes three routes: native
platform integration, developer-integrated capabilities and connected-platform
registry synchronization. **Supported native platforms use native integration
without adding the SDK**. Do not install an SDK merely to make a prompt agent's
inventory entry appear.

For code-level integration, the SDK adds **identity, governed Work IQ tooling
and notifications**. It does not build, host, deploy, select models, execute
tools or orchestrate agents. Microsoft Agent Framework remains a framework/
orchestration option; your runtime still applies application policy and executes
tool handlers. Some identity/notification capabilities require separate preview
eligibility or agent-user prerequisites; do not infer them from basic inventory.
These claims follow the [current SDK overview][sdk], not a workshop simulation.

**New observability uses the separate [Microsoft OpenTelemetry Distro][otel].**
Do not add deprecated Agent 365 observability SDK packages. Existing Foundry
documentation can retain earlier hosted-telemetry wording; use the current
observability guidance for a separately reviewed new integration or migration.
This lab does not install packages, migrate exporters or enable native export.
Application telemetry export configuration requires separate reviewed approval;
read-only native evidence consent does not grant it.

## What this application's tools and approvals are not

The separate PRESENTATION path in [the Azure live lab](azure-live-lab.md)
attaches four function definitions directly to a dedicated pinned prompt agent.
No Toolbox is required. Schemas may be visible in the Foundry portal, but its
playground does **not** execute the application's local function handlers.
Use the authorized application client loop to observe model-requested functions,
pre-execution policy and approved synthetic Search results.

Those functions are not native Agent 365 tooling or governed Work IQ access.
The local persistent live/local queue uses existing
`presentation_runtime.list_approvals(...)` and `approve_request(...)`.
Supplied action receipts remain DRY_RUN; role/reviewer labels remain
**SYNTHETIC_ROLE_LABELS_NOT_ENTRA_OBO** even when the model is live. Queue
persistence, separation of synthetic roles and an agent identity visible in a
portal do not supply authenticated enterprise business approval.

Creating the dedicated agent/index does not authorize publication, registry
mutation or consent. The initial verification's at-most-18-model-call budget is
shared across all chosen live examples; this native evidence lab does not need
extra model calls or attacks to produce a signal.

## Step-by-step read-only evidence collection

1. **Establish scope privately.** Confirm the intended tenant/cloud, Foundry
   account, agent type/version and authorized observer. Do not paste IDs, token
   claims, account output or portal screenshots into the notebook or public issues.
2. **Read the offline report first.** Notebook 05 imports `agent365.prerequisites`,
   `resource_status` and `verify_observations` with `Settings.local()`. UNKNOWN/
   VERIFICATION_REQUIRED are expected because no native evidence was collected.
3. **Authorize one setting read separately.** The notebook's preview confirmation
   approves only the existing `resource_status(..., preview_api=True)` operation.
   The documented `2026-03-15-preview` option is a read of account state, not a
   request to change properties. Missing permission remains a scoped gap.
4. **Review current license and existing consent.** Ask the responsible authorized
   administrator to confirm current requirements and already-established state.
   If missing, stop; do not purchase a license, accept terms or grant consent.
5. **Observe existing inventory and identity.** In the supported native
   administrative surface, locate the actual published agent, owner and sponsor.
   Distinguish the agent identity from the developer's credential principal.
   If no entry exists, report that scoped absence; do not publish/register it.
6. **Observe actual activity independently.** Use an existing authorized synthetic
   interaction and approved time window. Record the visible agent/workload scope
   and event time. An account setting or registry entry cannot replace an event.
7. **Inspect Defender/Purview separately if authorized.** Identify the supported
   workload and actual visible signal. No attack, policy change, Block/Unblock,
   alert-generation promise or fabricated event is part of this exercise.
8. **Verify private attestation records.** Apply the existing observation verifier
   to real records only. Scope/freshness/completeness checks are not authentication
   of the observer, linked evidence or remote service.

The [collection guidance][collection] makes account-level logging scope explicit:
contained projects/prompt agents inherit the setting. Do not toggle it to make a
single workshop agent look active. [Foundry integration guidance][integration]
also distinguishes workload creation, publication and activity collection. Native
capabilities may exist beyond this adapter's implemented reads; NOT_IMPLEMENTED
describes the adapter, not the whole Microsoft product.

```bash
uv run fsa agent365 preflight
uv run fsa agent365 status
# Optional read-only use of the specifically documented preview ARM API:
uv run fsa agent365 status --preview-api
uv run fsa agent365 verify --evidence path/to/private-observations.json
```

For the separate dedicated agent, use `--profile presentation` on the intended
read-only Agent 365 command, for example
`uv run fsa agent365 status --profile presentation`.
`uv run fsa azure agent-status --profile presentation` also targets that agent
rather than EQUIPMENT. Profile selection does not authorize preview reads,
publication, consent, RBAC or native logging changes. `uv run fsa --mode azure
audit verify`, `trace list` and `trace show S4` inspect retained LIVE application
evidence; they do not prove native registry/activity, Defender or Purview state.

Missing checks return nonzero and VERIFICATION_REQUIRED, not success.
Default local mode performs no Azure request. Azure account status requires the
configured resource group/account and selected Azure cloud. Field inspection uses
documented `2026-03-15-preview` only with explicit opt-in.

The commands above are references for an independently authorized operator, not
an instruction to run every read automatically. The Azure notebook remains
excluded from CI; expected UNKNOWN/PARTIAL evidence is not a runtime failure to
remove with stronger credentials.

## Optional read-only portal observation

In your own authorized environment, the workshop can include Agent 365 and
Defender portal observation without provisioning or administrative changes.
Keep tenant identifiers, identities, resource addresses and screenshots private.

- In Agent 365, inspect the actual inventory entry and its visible governance
  state. Record owner/sponsor, identity and activity only when actually visible;
  an inventory entry alone does not establish activity ingestion.
- In Defender, identify the visible resource or agent scope and observation
  time. Show existing findings only; do not generate attacks or promise an alert.
  A deployment finding is not automatically an agent-specific detection.
- Distinguish the portal evidence from local synthetic scenarios and DRY_RUN
  receipts. A portal observation does not validate the repository's adapters,
  Foundry IQ retrieval, or Monitor ingestion.
- If an expected item is absent or access is unavailable, retain that gap and
  continue with the labeled local exercises. Do not change consent, identity,
  Block/Unblock, policies or publication state during this observation.

## Separate observations

1. Confirm license and tenant consent independently.
2. Confirm prompt-agent publishing path and applicable identity.
3. In the supported Microsoft 365 administrative agent inventory, locate the
   actual agent and record its stable identifier and time.
4. Confirm Entra agent identity, owner and sponsor; do not substitute the app's
   DefaultAzureCredential caller for an agent identity.
5. Confirm an actual correlated activity event, not only a registry entry.
6. Review Defender and Purview independently; absence of a signal is not proof
   that no action occurred.

`Observation` JSON is an array with `capability`, `tenant`, `agent`, `observer`,
`observed_at` (UTC), `evidence_url`, `status`, `notes`. Required capabilities:
`license`, `consent`, `registry`, `identity`, `owner`, `sponsor`, `activity`.
Evidence must match the configured tenant/agent, be no older than 24 hours, and
have no duplicate capability. A resulting PASS means complete **operator
attestation**, never automated service validation. Keep observation files private
under ignored `artifacts/`; they can contain tenant and identity metadata.

Blocking/unblocking, disablement, retirement, MCP approval and consent changes
are NOT performed by the adapter. Use a documented synthetic walkthrough by
default; actual administrative action requires explicit independent authorization.
Hosted agents have separate SDK/telemetry requirements; this lab selects a
prompt agent. Government/GCC/GCC High/DoD availability is VERIFICATION_REQUIRED.

## Interpret results, questions and cleanup

| Observation | Supported interpretation | Unsupported inference |
|---|---|---|
| Logging true/status Enabled | Existing account settings report enablement | Actual activity ingested |
| Published entry visible | Scoped inventory observation at that time | Runtime tools or enterprise approval validated |
| Owner/sponsor visible | Governance metadata observed | Those people approved a business request |
| Correlated native activity | That event is visible in that scope/window | Defender alert/Purview enforcement occurred |
| Operator attestation PASS | Supplied evidence meets verifier rules | Automated API/service validation |
| Missing access or event | Evidence gap remains | A guessed license or cloud-support cause |

Explain why the SDK is unnecessary for a supported native inventory route.
Identify which selected capabilities would require developer SDK integration,
and which would require the separate observability distro. Why cannot a local
queue approval or Monitor span stand in for native activity? These are design/
evidence questions, not invitations to install, consent or publish.

Use the minimum read access needed for the specific surface. A failed read is
not authority to elevate privileges. Native licensed capabilities, retention and
queries can have separate costs; reading guidance does not enable them. Keep
private observation records only for the approved retention window, clear
notebook outputs and restart the kernel to discard loaded settings. No cloud
resource deletion, agent retirement or native cleanup runs here.

## Verified sources and official repositories

References checked 2026-11-12; original explanations above, no copied source:

- [Agent 365 SDK overview][sdk]: native versus SDK integration; identity/tooling/
  notifications rather than orchestration; deprecated observability warning.
- [Microsoft OpenTelemetry Distro][otel]: separate current observability.
- [Foundry integration][integration]: publication/registry and collection boundaries.
- [Foundry data collection][collection]: account settings, inheritance and
  independent license/consent prerequisites.
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework):
  framework source, distinct from Agent 365 integration.
- [Agent 365 Python SDK](https://github.com/microsoft/Agent365-python):
  developer integration source; not a new registry API for this adapter.
- [Microsoft OpenTelemetry Python](https://github.com/microsoft/opentelemetry-distro-python):
  current distro source, not a package installed by the lab.
- [Azure AI Projects SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects):
  Foundry client contracts, not evidence of tenant success.

[sdk]: https://learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-sdk?tabs=python
[otel]: https://learn.microsoft.com/en-us/microsoft-agent-365/developer/microsoft-opentelemetry
[integration]: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-365-integration
[collection]: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/configure-agent-365-data-collection
