# Workshop notebooks

## Start here

From the repository root, in Bash or PowerShell:

```text
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
```

Use Python 3.12. Open the repository folder in VS Code with the Python and
Jupyter extensions. Open a notebook, choose **Select Kernel -> Python
Environments -> the repository `.venv` interpreter**, then run cells in order.
The generic kernel display name is not proof that the right interpreter is
selected; notebook 00 checks it. Installation needs package access once.

## Recommended path: Azure Live workshop

Complete 00, then follow [Azure setup](../docs/participant-lab/azure-live-lab.md)
and notebook 01's **PRESENTATION** review/setup/invocation cells. Reuse an approved
dedicated agent/index when your owner has already prepared them; do not recreate
or overwrite them. Continue 02 -> 03 -> 04, selecting only the live exercises
covered by your session's permissions, data/egress consent and model budget.
Notebook 05 is an optional native-governance observation extension, not a
prerequisite for Foundry/Search.

Azure-first is the recommended learning order, **not an execution default**.
All live switches remain OFF until deliberately changed. Do not Run All with
live cells enabled. Local negative controls and DRY_RUN receipts remain local
even in an Azure workshop.

## Azure unavailable: local, credential-free fallback

| Order | Notebook | What to observe |
|---|---|---|
| 1 | [00 Setup](00_environment_setup.ipynb) | Package/kernel checks pass; Azure NOT_CHECKED |
| 2 | [02 Protect](02_protect_identity_and_tools.ipynb) | Policy, access and injection denials; DRY_RUN approvals |
| 3 | [03 Prove](03_prove_evaluations_and_redteam.ipynb) | Safe PASS; deliberately unsafe FAIL; evidence reconciliation |
| 4 | [04 Operate](04_operate_traces_and_audit.ipynb) | Local trace inspection and audit-copy tamper rejection |

[06 Local walkthrough](06_local_fallback.ipynb) is a consolidated alternative
after setup, including local lifecycle simulation.
The six local notebooks, including [07 Lifecycle](07_agent365_request_approval_publish.ipynb),
support Run All. **Every added live cell defaults to
`RUN_AZURE_LIVE=False`**, with imports, private configuration, variables and
`input()` confirmation inside the guarded branch. Local execution must not
acquire credentials or use services.
Restart the kernel before repeating a lab. Keep the synthetic/DRY_RUN labels.

## Azure exercises: run cell by cell

- [01 Azure Live](01_foundry_agent_live.ipynb): keeps the existing no-tools
  **EQUIPMENT compatibility** validator (at most two model calls per invocation),
  with separate IQ discovery consent. Adds independent review, explicitly
  authorized **NEW dedicated PRESENTATION setup**, and a bounded live question.
  IQ discovery is not retrieval.
- [05 Agent 365](05_agent365_extension.ipynb): its first code cell is offline.
  The optional account-setting read asks for explicit authorization. Portal
  registry/activity/Defender observations are independent acceptance tasks.
- [02 Protect](02_protect_identity_and_tools.ipynb): keeps the original
  default-off equipment Search/moderation checks and adds a separately consented
  presentation function/policy example.
- [03 Prove](03_prove_evaluations_and_redteam.ipynb): adds a safe live six-scene
  regression, at most three model calls per scene, displaying only actually
  returned observations. Cloud judging is a reference-only separate exercise.
- [04 Operate](04_operate_traces_and_audit.ipynb): adds independent default-off
  live invocation and read-only `query_azure_traces` cells. Application export,
  Azure Monitor ingestion and native Agent 365 activity are different evidence.
- [00 Setup](00_environment_setup.ipynb): adds consented **configuration-only**
  Azure Settings validation; no credentials, service requests or identifiers.

Do not use unattended Run All for 01/05. Declining consent raises PermissionError
by design. Missing telemetry can produce PARTIAL in 01; status reporting preserves
that gap instead of asserting universal success. Stop and inspect the actual
checks rather than bypassing them. Missing IQ
configuration is a real gap, not evidence that the notebook itself is broken.
Only the separate, explicitly authorized presentation setup can create resources:
one NEW dedicated synthetic index and NEW dedicated function-tool agent. No cell
deploys shared infrastructure, publishes an agent, changes consent or RBAC, or
configures native governance.

## Local Agent 365 lifecycle scenario

[07 Request -> approval -> publication](07_agent365_request_approval_publish.ipynb)
is a standalone local lab after 00, useful alongside 05 or after the core flow.
It reuses the actual lifecycle model: seven evidence checks, independent exact
approval, DRY_RUN publication, bounded 180-day synthetic package, denied
out-of-package reads/writes, rejected v2 and an actual retained-v1 read.
The [participant lab](../docs/participant-lab/request-approval-publish.md)
explains maker routes, the native wizard, role boundaries, activation-only
templates, report-only CA and optional read-only observation. No notebook
changes templates, consent, attributes, packages, CA state or publication.

## Keep the two Azure profiles separate

| Property | EQUIPMENT compatibility | PRESENTATION live |
|---|---|---|
| Agent/index settings | Existing equipment settings, unchanged | Separate `presentation_*` fields |
| Agent definition | Pinned prompt agent without remote tools | Pinned prompt agent with four function definitions |
| Tool selection | Fixed application-controlled operation | Actual model function-call requests |
| Tool execution | Existing governed application path | Client handlers, after pre-execution policy |
| Evidence source | Approved synthetic equipment corpus | Dedicated approved synthetic presentation corpus |
| Action boundary | Existing approval/DRY_RUN path | Local persistent approval queue, supplied receipts DRY_RUN |

PRESENTATION defaults are `presentation_agent_name=contoso-policy-assistant` and
`presentation_search_index=fsa-presentation-synthetic`.
`presentation_agent_version` must be pinned to the actual version returned by
authorized setup; never use mutable latest or overwrite equipment settings.
If a dedicated name is already in use, stop for ownership/name review rather
than treating it as permission to reuse, update or delete that resource.

The implementation used by the added cells is
`foundry_security_accelerator.presentation_live`:

- `review(settings) -> dict`: inspect the returned review facts/plan; not setup.
- `setup(settings, authorized=False) -> dict`: no creation authorization by default.
- `run_question(settings, text, role, state_dir, authorized=False) -> dict`:
  bounded real-model execution; private local evidence/queue state.
- `run_scenes(settings, state_dir, authorized=False) -> dict`: six safe scenes,
  at most three model calls each.

These are workshop contracts, not invented Microsoft platform APIs. The four
functions—`search_policies`, `get_policy_section`, `get_ticket_status` and
`create_records_request`—are attached directly. **No Toolbox is required.**
Schemas can be visible in the Foundry portal, but **the playground does not
execute this application's local function handlers**. Use the authorized client
loop to observe execution. A model requesting a function does not authorize it.

The serial runtime allows at most **three model requests and six proposed tool
calls per scene/question**; the third/final round uses `tool_choice=none`.
`run_question` reports `status`, `model_calls`, `tool_calls`, `citations`,
`quarantined_sections`, `correlation_id`, `audit`, `audit_head`, `audit_verified`,
`trace_path` and `trace_export_status`. Do not use the EQUIPMENT field names
`traces` or `telemetry_export` for PRESENTATION. `run_scenes` returns `status`,
`scenes` and `manifest_path`, with structural per-scene checks—not judge scores.

## Consent, identity and the current verification budget

Plan initial verification with **at most 18 model calls total** against the
existing private project and dedicated presentation resources. This is not a
per-notebook allowance. Choose a full six-scene run *or* a smaller set of examples;
deduct previous calls, including other validator/model runs. Do not spend part of
the budget and then automatically launch an 18-call suite. Do not retry until
PASS. The editing/contract-validation process does not run cloud cells.

Native scope is **read-only evidence checks and detailed portal/SDK guidance;
native configuration changes are excluded**. Licensing, publishing, tenant
consent, role assignments, registration, logging changes and lifecycle mutations
need independent authorization outside these labs. A request to “check integration”
is not permission to repair it.

Telemetry export configuration requires **separate reviewed approval**.
Added invocation cells require an independent default-off opt-in and confirmation
for already-configured Monitor/OTLP egress; invocation consent alone is insufficient.
The read-only query cell can inspect an independently authorized existing run;
it cannot enable export, and it may legitimately find no rows.

All live/local role labels remain **SYNTHETIC_ROLE_LABELS_NOT_ENTRA_OBO**.
The shared queue is accessed by the existing
`presentation_runtime.list_approvals(...)` and `approve_request(...)`; consult
their documented inputs before any separately authorized local review. No added
cell automatically approves a request. Queue persistence and an independent
synthetic role do not establish authenticated enterprise approval.

## Interpreting results and troubleshooting

| Result | Interpretation |
|---|---|
| NOT_EXECUTED | Switch/consent prevented the optional operation; no cloud result |
| Local PASS | Selected local fixtures passed; no cloud claim |
| UNKNOWN / PARTIAL / VERIFICATION_REQUIRED | Preserve the scoped evidence gap |
| Pending approval | No business action has been authorized by that state alone |
| DRY_RUN | Supplied writer recorded simulation, not a remote write |
| SENT_NOT_INGESTION_PROOF | Application export report, not destination visibility |
| Correlated Logs rows | Application telemetry in that workspace/window, not native A365 |
| Operator attestation PASS | Supplied scoped/fresh observations checked, not API validation |

An exception remains a real error; do not silently select local mode or fabricate
success. Use 06 explicitly when cloud access is unavailable. **06 remains LOCAL**
even when presenting other labs live. The unsafe negative control in 03 is local
in-memory simulation only; never extend it into a remote attack or bypass.

In a private authorized terminal, inspect retained LIVE evidence separately:

```text
uv run fsa --mode azure audit verify
uv run fsa --mode azure trace list
uv run fsa --mode azure trace show S4
uv run fsa azure agent-status --profile presentation
uv run fsa agent365 status --profile presentation
```

Azure audit verification reads the latest LIVE session; trace list/show reads
actual saved live scenes/spans, not local fixtures. An absent S4 remains absent.
Use `--profile presentation` for Agent 365 commands intended for the dedicated
agent; keep preview-read authorization separate. Saved application evidence is
not export delivery, ingestion, native activity or a Defender/Purview finding.

For import errors, select the prepared repository kernel rather than installing
packages in cells. For access errors, preserve the narrow failure and request an
owner review; do not broaden roles. Each code cell has preceding guidance on its
actual implementation, inputs, outputs, assertions, limits and troubleshooting.

## Validation and help

The local validator checks all eight notebook contracts/imports, executes only
the six allowlisted local notebooks under network/credential denial, and
keeps source outputs empty:

```text
uv run python scripts/validate_notebooks.py --execute-local
```

Azure notebooks are not executed in PR CI. Passing local validation does not
establish live cloud success.

For a documentation-only contract/import check without executing any notebook:

```text
uv run python scripts/validate_notebooks.py
```

The validator resolves imports even inside default-off branches, so an unavailable
new API can block contract validation without any live cell having run.

## Current Microsoft guidance and official source references

References verified 2026-11-12:

- [Function calling](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling):
  the model requests functions; the application executes and returns results.
- [Search RBAC](https://learn.microsoft.com/en-us/azure/search/search-security-rbac):
  read/query, index management and content-write permissions are distinct.
- [Agent 365 SDK overview](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/agent-365-sdk?tabs=python):
  supported platforms use native integration without adding the SDK; SDK
  capabilities are identity, governed Work IQ tooling and notifications—not
  orchestration, hosting or model selection.
- [Microsoft OpenTelemetry Distro](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/microsoft-opentelemetry):
  separate current observability integration; **do not add deprecated Agent 365
  observability SDK packages**.
- Official source repositories:
  [Microsoft Agent Framework](https://github.com/microsoft/agent-framework),
  [Azure AI Projects](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects),
  [Agent 365 Python](https://github.com/microsoft/Agent365-python), and
  [Microsoft OpenTelemetry Python](https://github.com/microsoft/opentelemetry-distro-python).
  Links support further study, not unreviewed installation or copied sample code.

See the [participant guide](../docs/participant-lab/README.md),
[Azure prerequisites](../docs/participant-lab/azure-live-lab.md),
[troubleshooting](../docs/participant-lab/troubleshooting.md), and
[cleanup](../docs/participant-lab/cleanup.md).
Clear all outputs before sharing; `.fsa`, `artifacts` and private `.env` must
remain local.

**Workshop only, not production or WAF certification.** Read the
[production/Well-Architected Framework disclaimer](../docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).
