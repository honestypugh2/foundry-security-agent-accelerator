# Azure participant lab

## Recommended workshop route: existing project, separate profiles

Complete [00 setup](../../notebooks/00_environment_setup.ipynb) first; completing
the local core labs is not a prerequisite.
Read the [production/WAF disclaimer](README.md#production-and-well-architected-framework-waf-disclaimer).
The following service calls require your own authorization and may incur cost.

Duration 20-45 minutes; L300-L400. Use [notebook 01](../../notebooks/01_foundry_agent_live.ipynb)
after [setup](../../notebooks/00_environment_setup.ipynb).
Verify the existing Search/Foundry path in your own authorized environment.
Monitor ingestion and Foundry IQ retrieval each need independent evidence;
neither follows from a working ordinary Search query. No resources need to be
recreated when the required existing services are already configured.

The primary route is **PRESENTATION live**, the dedicated four-function path
below. The original **EQUIPMENT compatibility** notebook cells run the bounded
end-to-end live validator. Its status is
PARTIAL if telemetry is missing; this is not a full integration PASS.
Notebook 02 also has an optional OFF-by-default live Search/moderation section.
[Demo-story documents](../../data/synthetic/demo-search-documents.json) are
staged locally only. Upload and IQ source/base creation need separate reviewed
authorization; no notebook performs them automatically.

Bash:
```bash
uv sync --frozen --all-extras --dev
test -e .env || cp .env.example .env
# Configure only your own approved existing resources in ignored .env.
az login
# Select your authorized cloud/subscription privately; do not capture account output.
uv run python -m fsa --mode azure doctor
uv run python -m fsa azure whoami
uv run python -m fsa azure preflight
```

PowerShell:
```powershell
uv sync --frozen --all-extras --dev
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
az login
# Select your authorized cloud/subscription privately.
uv run python -m fsa --mode azure doctor
uv run python -m fsa azure whoami
uv run python -m fsa azure preflight
```

Doctor validates configuration, not service connectivity. Whoami reports redacted
CLI selection, not the SDK's effective credential. Preflight normally returns
nonzero with unresolved capabilities; review them, do not bypass them. No
inference has been authorized by these configuration/read checks. Continue with
the presentation profile below. Failure remains failure, never automatic local
success. Use the [local fallback](local-fallback.md) explicitly if prerequisites
are unavailable. Cloud usage is billable.

### Prepare your private configuration

Start from [.env.example](../../.env.example); preserve safe local defaults and
select Azure explicitly in commands. Edit only your private ignored `.env`.

| Configuration group | What you supply | Verify with your resource owner |
|---|---|---|
| Cloud and identity | Authorized cloud, tenant/subscription, resource group/account/project | Correct cloud/region and CLI selection; supported services and network path |
| Foundry inference | Project endpoint and actual model deployment | Model availability/quota, least-privilege invocation permissions and cost |
| Synthetic Search | Search endpoint and reviewed dedicated presentation index | Query-only access for participants; separate setup/upload permissions |
| Dedicated agent | Presentation name and immutable returned version | Ownership, reviewed instructions and exactly four expected function schemas |
| Optional moderation/telemetry/evaluation | Only settings approved for the selected exercise | Separate data egress, access, licensing and spending authorization |

Never print private configuration or reuse another tenant's identifiers.
An owner may prepare the dedicated resources once and provide approved private
settings to participants; query-only participants must not run setup. This
application is an ordinary prompt agent with caller-side Python function
handlers, not a hosted agent or managed Copilot harness.

## PRESENTATION live: dedicated four-function path

This is a different experiment from the no-tools equipment agent. The existing
private project/model may be used within the approved scope, but the equipment
agent/index settings must remain unchanged. Dedicated defaults are:

| Settings field | Intended value / handling |
|---|---|
| `presentation_agent_name` | `contoso-policy-assistant`, a NEW dedicated agent |
| `presentation_search_index` | `fsa-presentation-synthetic`, a NEW dedicated index |
| `presentation_agent_version` | Actual immutable version returned by authorized setup |

Use the existing private Settings configuration mechanism; this guide does not
edit `.env`, echo configuration or reuse another presenter's identifiers.
If a dedicated name is already in use, stop for ownership/name review. Do not
overwrite, delete, upload into or silently adopt an existing resource.

### Review, then authorize setup independently

Read [notebook 01](../../notebooks/01_foundry_agent_live.ipynb) for separate
default-off review/setup/invocation cells. The equivalent application commands
below are reference instructions, not commands run by the documentation update:

```text
uv run fsa azure presentation-review
# Only after reviewing exact NEW dedicated resources, corpus, roles and cost:
uv run fsa azure presentation-setup --authorize
# Inspect returned setup evidence privately and pin presentation_agent_version.
```

`review(settings) -> dict` reports review facts/plan; it is not creation.
`setup(settings, authorized=False) -> dict` is explicitly unauthorized by default.
Authorized setup may create only the NEW dedicated index/agent and populate the
approved synthetic corpus. It must not recreate shared infrastructure, change the
equipment path, grant roles, configure native logging, accept tenant terms or
publish/register an agent. Keep actual returned resource/version evidence private;
partial setup is not permission to retry against arbitrary existing resources.

Query-only participants need narrow Foundry invocation access and Search query
permissions. Index/object creation, synthetic document upload and agent creation
need separately reviewed setup rights. [Search RBAC documentation][search-rbac]
distinguishes Search Index Data Reader, Search Service Contributor and Search
Index Data Contributor; a data-reader role alone does not permit setup. Review
the exact scopes rather than granting broad subscription or tenant administration.
No role changes are performed by this lab.

### How function execution differs from EQUIPMENT

The agent has four function definitions attached **directly**:

| Function | Intended boundary |
|---|---|
| `search_policies` | Approved synthetic policy Search corpus only |
| `get_policy_section` | Approved eligible synthetic section, not arbitrary source expansion |
| `get_ticket_status` | Synthetic ServiceDesk evidence, not a production ticket connector |
| `create_records_request` | Policy-gated local persistent approval request, not remote execution |

The actual Azure model requests function calls. The client validates each name
and arguments and enforces pre-execution policy before executing a handler or
returning a result. Function selection and natural-language confidence cannot
grant entitlements or approval. This client-execution pattern is described in
[Microsoft's function-calling guidance][function-calling].

**No Toolbox is required.** Function schemas may be visible in the Foundry portal,
but the playground does **not** execute this application's local Python handlers.
Use the application loop, not a portal chat, to demonstrate policy-controlled
execution. These functions are also not governed Work IQ tools or native Agent
365 SDK integration merely because they appear on an agent definition.

The corresponding workshop APIs are
`presentation_live.run_question(settings, text, role, state_dir, authorized=False)`
and `presentation_live.run_scenes(settings, state_dir, authorized=False)`, both
returning dictionaries with actual observed evidence. No fake platform endpoint
is involved. The approved synthetic corpus is the only eligible Search source;
do not upload customer data with a synthetic label or broaden retrieval to make
an answer more convincing.

The runtime is serial, bounded to three model requests and six proposed tool
calls per scene/question; the third/final round uses `tool_choice=none`.
`run_question` reports `status`, `model_calls`, `tool_calls`, `citations`,
`quarantined_sections`, `correlation_id`, `audit`, `audit_head`, `audit_verified`,
`trace_path` and `trace_export_status`. The last two are PRESENTATION fields,
not the EQUIPMENT API's `traces`/`telemetry_export`. `run_scenes` returns `status`,
`scenes` and `manifest_path`, with structural per-scene checks rather than
model-judge scores. Expected denials and real failures must both be reported
truthfully.

### Invoke deliberately; budget across the session

```text
# Choose this bounded six-scene suite OR a smaller set of questions:
uv run fsa demo --mode azure --profile presentation --authorize
# Separate optional question; it also consumes the same session budget:
uv run fsa ask --mode azure --profile presentation --authorize --as employee "Summarize the synthetic retention policy and cite the approved policy section."
```

The six-scene suite has **at most three model calls per scene**. The planned
initial verification ceiling is **at most 18 model calls total across the initial
verification**, not 18 per command or notebook. Deduct previous model/validator
calls. A full suite is not automatically authorized after earlier questions have
consumed budget; choose a smaller plan or stop for review. A denied request may
use zero calls. Search and any independently approved services can add cost.
No retry-until-PASS loop is included.

Inspect saved LIVE evidence separately in an authorized private terminal:

```text
uv run fsa --mode azure audit verify
uv run fsa --mode azure trace list
uv run fsa --mode azure trace show S4
uv run fsa azure agent-status --profile presentation
uv run fsa agent365 status --profile presentation
```

Audit verification reads the latest LIVE session; trace list/show reads actual
saved live scenes/spans. An absent scene remains absent, not a local fixture
substitution. PRESENTATION profile selectors keep agent-status/native reads
separate from EQUIPMENT. Preview account reads still need their own authorization.
Saved spans, export status, workspace ingestion and native observations remain
distinct; these commands do not configure export or mutate native state.

The role is explicitly **SYNTHETIC_ROLE_LABELS_NOT_ENTRA_OBO**, even in Azure mode.
It is not the authenticated enterprise identity of the caller or reviewer.
The live/local persistent queue is shared through existing
`presentation_runtime.list_approvals(...)` and `approve_request(...)`.
Consult their documented inputs and exact state directory before separately
authorized synthetic review; no notebook automatically approves a request.
An independent synthetic role label is still not authenticated enterprise
approval. The supplied writer produces **DRY_RUN only**, never a real records
write. Queue persistence does not change that limit.

### Current telemetry and native scope

Native scope is **read-only evidence checks and detailed portal/SDK guidance;
native configuration changes are excluded**. Publishing, registration, licensing,
consent, RBAC, native policy and logging mutations are not authorized. The
Agent 365 extension in 05 observes existing settings and separate native evidence.

**Telemetry export configuration requires separate reviewed approval**.
Added presentation invocation cells require independent default-off consent for
already-configured Monitor/OTLP egress; they never enable/configure exporters.
For the existing EQUIPMENT validator, do not opt into configured export unless
its exact destination, content, retention and cost were independently approved. Missing
ingestion may therefore correctly remain PARTIAL. The read-only query in 04 can
inspect a separately authorized existing application run; it does not enable
export. Keep local spans, export status, queried Monitor rows and native Agent 365
activity as different observations.

### Notebook-by-notebook live alternatives

- **00:** consented Settings validation only, with no repr/dict, identifiers,
  credential acquisition or endpoint request.
- **01:** independent review, NEW dedicated setup and one bounded question.
  Original EQUIPMENT and IQ steps retain their own authorization boundaries.
- **02:** compare local controls with a consented real function/policy run;
  pending records requests are not auto-approved.
- **03:** consented safe `run_scenes`, summarizing actually returned status/
  decision/call-count evidence, not fabricated scores. A cloud semantic judge is
  optional and reference-only via [existing evaluation API instructions](../evaluations/foundry-service.md).
  The unsafe local negative control must never become a remote attack bypass.
- **04:** separate live invocation from `query_azure_traces` and native evidence.
- **05:** read-only native evidence, licensing/publication/consent review and
  current SDK/portal guidance; no mutations.
- **06:** explicitly **LOCAL fallback**, never relabeled live.

All new live branches in CI-local notebooks are committed False, initialize their
own variables inside the branch and prompt only after opt-in. CI also denies
sockets and credentials independently. An import check can pass without any
cloud execution; it cannot establish live success.

### Interpretation, exercises and cleanup

| Observation | Supported claim | Unsupported claim |
|---|---|---|
| Review result | Scoped review facts returned | Resources created |
| Setup version returned | Actual setup evidence available to pin | Published/native registry entry |
| Model requests function | Model selected a candidate operation | Authorized execution |
| Policy blocks function | Client denied that operation | Universal injection immunity |
| Queue request pending | Local persistent review item exists | Enterprise approval or remote write |
| Live PARTIAL / UNKNOWN | Evidence gap remains | Runtime success or automatic fallback |

Explain where client policy runs relative to a model function call. Compare a
safe citation with an approved action: why cannot the first imply the second?
Identify the independent evidence required for Monitor ingestion, native activity
and authenticated approval. These questions require no extra cloud calls.

Retain private state and returned resource/version evidence until review.
Clearing a queue or deleting a local directory is not cloud cleanup or native
retirement. Inventory only the exact dedicated resources created for this run;
obtain separate authorization before deletion. Never delete the equipment agent,
shared index, model deployment, account or resource group for convenience.

[function-calling]: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling
[search-rbac]: https://learn.microsoft.com/en-us/azure/search/search-security-rbac Cloud usage is billable.
`agent run` is the distinct direct invocation path without application controls;
do not substitute it for `ask`. Synthetic roles are not Entra/OBO.

For missing project/model/agent/index, stop and request separately authorized
setup; the reference provisioning sections below are not session-day actions.
The compatibility commands do not automatically create an agent, deploy, publish,
register, or change permissions/logging/consent. The separate PRESENTATION setup
below requires independent explicit authorization for NEW dedicated resources
only. See [cleanup](cleanup.md) and [troubleshooting](troubleshooting.md).

## Prerequisites and authorization

Use your own authorized tenant/subscription and **new Microsoft Foundry project**,
not a classic hub-based project. Confirm Foundry prompt-agent support,
regional model quota, effective project permissions, Search availability and
network access. Agent 365, Defender, Purview and Sentinel are optional independent
licensed integrations. Local tests need none of them.

Use Entra ID, not API keys. Search needs **Search Index Data Reader** for queries;
creating or populating an index requires separate explicitly authorized roles.
Foundry project operations require the current applicable Foundry data-plane
role. Resource creation additionally needs suitable Azure Contributor scope.
Do not grant tenant-wide administrator roles for this lab.

## EQUIPMENT compatibility: existing-project path

Bash:
```bash
uv sync --frozen --all-extras --dev
test -e .env || cp .env.example .env
az login
az cloud show
az account show
# Explicitly select your approved cloud and subscription yourself before continuing.
```

PowerShell:
```powershell
uv sync --frozen --all-extras --dev
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
az login
az cloud show
az account show
```

Edit ignored `.env`: `FSA_MODE=azure`, tenant/subscription, project endpoint,
model deployment, agent name/version, Search endpoint/index. Optional Content
Safety endpoint enables additional input/output moderation. Local mode never
contacts these services even if endpoints are present.

The Search index must contain these retrievable fields: `source_id`, `title`,
`content`, `entitlement`, `classification`; `entitlement` is a filterable string.
Only original synthetic lab documents with `classification=synthetic` are
accepted. Use `equipment-001`, `employee`, and the synthetic policy fixture.
No automatic index creation or content upload is performed.

```bash
uv run fsa azure preflight
# Resolve every UNKNOWN / VERIFICATION_REQUIRED item; account match is not quota proof.
uv run fsa agent deploy
# After explicit authorization to create a prompt-agent version:
uv run fsa agent deploy --authorize
# Store the returned version as FSA_AGENT_VERSION; do not use mutable "latest".
uv run fsa demo --mode azure
```

Invocation verifies that the pinned version is a prompt agent with no remote
tools and matches the configured model deployment. Response text cannot execute
the writer or approve a proposal. Expected status is `AWAITING_APPROVAL`, not a
real business write. Cloud failures propagate and never become synthetic success.

## Separately authorized administrator reference: new resources

This is not required for the workshop and is **outside the current approved
scope**. Dedicated presentation setup above is not permission to execute this
reference. Do not execute provisioning commands as
part of the local labs or modify shared resources. Obtain a reviewed cost,
security and deployment plan before any cloud changes.

The default resource-group Bicep creates an AI Services account/project with
local-key auth disabled and managed identity. Optional `enableLiveServices`
adds a parameterized GA model, Entra-only Search and Content Safety; optional
`enableMonitoring` adds Logs/Insights. A nonempty approved `principalId` with
live services enabled adds five explicit resource-scoped operator grants when
monitoring is also enabled. The template assumes that principal is a user.
Do not grant roles to a different principal type by changing the ID alone.
No private endpoints, tenant consent or publishing are implemented.
Public network access is enabled for the teaching template: do not call it
private-network hardened.

```bash
az bicep build --file infra/main.bicep --stdout
az deployment group what-if --resource-group YOUR_GROUP --template-file infra/main.bicep \
  --parameters name=YOUR_UNIQUE_ACCOUNT location=YOUR_APPROVED_REGION
# Review cost and changes; ONLY AFTER explicit authorization:
az deployment group create --resource-group YOUR_GROUP --template-file infra/main.bicep \
  --parameters name=YOUR_UNIQUE_ACCOUNT location=YOUR_APPROVED_REGION
```

PowerShell uses the same arguments on one line or backticks instead of backslashes.
The resource group must already exist. Model availability and quotas are regional;
the default command above does not enable live services. Configure the supported
deployment and Search before invoking, or review/authorize the optional parameters.
Bicep compilation
does not establish Azure acceptance, capacity or successful creation.

For an explicitly approved **new isolated group**, the subscription entry
[live.bicep](../../infra/live.bicep) enables the synthetic lab services and
monitoring. Prepare a private parameter file with `resourceGroupName`, `location`,
`searchLocation`, `principalId`, `modelName`, `modelVersion`,
`modelDeploymentName` and `modelCapacity`. Confirm regional availability and cost;
never reuse a presenter's identifiers or overwrite existing private settings.

```bash
az bicep build --file infra/live.bicep --stdout
az deployment sub validate --location YOUR_REGION --template-file infra/live.bicep --parameters @YOUR_PRIVATE_PARAMETERS
az deployment sub what-if --location YOUR_REGION --template-file infra/live.bicep --parameters @YOUR_PRIVATE_PARAMETERS
# Review exact changes and obtain explicit authorization before deployment:
az deployment sub create --location YOUR_REGION --template-file infra/live.bicep --parameters @YOUR_PRIVATE_PARAMETERS
```

Verify the project resource and each actual assignment's `scope` after
deployment; do not infer least privilege from role names alone. Keep the model
content-filter policy. Search may require a separately approved alternate region.
Any prior commercial exercise is not current participant verification and is not
Government proof.

## Evidence and cleanup

Run local security/evaluation regressions and inspect hash-linked audit and local
OTel files. Azure Monitor export configuration requires separate reviewed approval. A future exporter result would still require independent
ingestion evidence from the target workspace.

Inventory resources with `az resource list --resource-group YOUR_GROUP`.
Review exact resource IDs and dependencies, then explicitly authorize individual
resource deletion yourself. Never delete a shared group. No cleanup command runs
automatically. Azure resources, model inference, Search, Content Safety and
monitoring can incur cost until separately removed or disabled.

## Current official references

Verified 2026-11-12. [Agent 365 SDK overview](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-sdk?tabs=python)
states that supported platforms use native integration without adding the SDK.
Developer SDK capabilities are identity, governed Work IQ tooling and
notifications—not orchestration, hosting or model selection.
[Microsoft OpenTelemetry Distro](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/microsoft-opentelemetry)
is the separate current observability integration; **do not add deprecated Agent
365 observability SDK packages**. This guide installs neither.

Official source repositories:
[Microsoft Agent Framework](https://github.com/microsoft/agent-framework),
[Azure AI Projects SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects),
[Agent 365 Python SDK](https://github.com/microsoft/Agent365-python), and
[Microsoft OpenTelemetry Python Distro](https://github.com/microsoft/opentelemetry-distro-python).
These support the respective framework/client/integration/observability
boundaries; no source code is copied or tenant validation implied.
