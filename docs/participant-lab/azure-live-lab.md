# Azure participant lab

## Optional lab: existing resources, no deployment

Complete the [local core labs](README.md#lab-order-and-expected-outcomes) first.
Read the [production/WAF disclaimer](README.md#production-and-well-architected-framework-waf-disclaimer).
The following service calls require your own authorization and may incur cost.

Duration 20-45 minutes; L300-L400. Use [notebook 01](../../notebooks/01_foundry_agent_live.ipynb)
after [setup](../../notebooks/00_environment_setup.ipynb).
Verify the existing Search/Foundry path in your own authorized environment.
Monitor ingestion and Foundry IQ retrieval each need independent evidence;
neither follows from a working ordinary Search query. No resources need to be
recreated when the required existing services are already configured.

The notebook now runs the bounded end-to-end live validator. Its status is
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
uv run python -m fsa --mode azure ask "Explain synthetic equipment policy." --as analyst
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
uv run python -m fsa --mode azure ask "Explain synthetic equipment policy." --as analyst
```

Doctor validates configuration, not service connectivity. Whoami reports redacted
CLI selection, not the SDK's effective credential. Preflight normally returns
nonzero with unresolved capabilities; review them, do not bypass them. Ask uses
the governed workflow and should stop at AWAITING_APPROVAL; failure remains
failure, never automatic local success. Cloud usage is billable.
`agent run` is the distinct direct invocation path without application controls;
do not substitute it for `ask`. Synthetic roles are not Entra/OBO.

For missing project/model/agent/index, stop and request separately authorized
setup; the reference provisioning sections below are not session-day actions.
No automatic agent creation, deployment, registry, permission, logging or consent
change is included. See [cleanup](cleanup.md) and [troubleshooting](troubleshooting.md).

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

## Existing-project path

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

This is not required for the workshop. Do not execute provisioning commands as
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
This lab was successfully exercised commercially; it is not Government proof.

## Evidence and cleanup

Run local security/evaluation regressions, inspect hash-linked audit and OTel
files, and optionally enable Azure Monitor export only after privacy/egress
review. Monitor delivery requires independent evidence from the target workspace.

Inventory resources with `az resource list --resource-group YOUR_GROUP`.
Review exact resource IDs and dependencies, then explicitly authorize individual
resource deletion yourself. Never delete a shared group. No cleanup command runs
automatically. Azure resources, model inference, Search, Content Safety and
monitoring can incur cost until separately removed or disabled.
