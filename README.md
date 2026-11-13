![Microsoft Foundry + Security + Agent 365 — Protect. Prove. Operate. Enterprise AI Agents.](docs/assets/readme-banner.png)

# Foundry + Security + Agent 365 Workshop

**Protect. Prove. Operate.** Hands-on Python labs for a governed agent workflow.
Use the **Azure Live workshop path** with your own authorized environment.
If Azure, permissions, quota, or product availability are missing, explicitly
choose the **local fallback** and complete the same security learning objectives
without claiming Azure execution.

> Azure governs the infrastructure. Foundry governs the AI workload.
> Agent 365 governs the deployed agent. Report centrally. Enforce natively.

This repository contains original synthetic examples. There is no presenter
tenant dependency. Local execution is not Azure validation, and application
telemetry is not Agent 365 activity-ingestion evidence.

> **Workshop, not production:** this accelerator is not production-ready,
> a security/compliance certification, or an Azure Well-Architected Framework
> (WAF) assessment. See the [production disclaimer](docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).

## 1. Prerequisites and workshop setup

| Requirement | Azure Live path | Local fallback |
|---|---|---|
| Python **3.12**, Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) | Required | Required |
| VS Code with Python and Jupyter extensions | Required for notebooks; CLI also supported | Same |
| Package download access during initial setup | Required once for the frozen environment | Required once, then exercises are offline |
| [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and interactive sign-in | Required for the documented Azure setup | Not required; no credentials acquired |
| Authorized tenant/subscription and supported cloud/region | Required; verify quota and service/network access | Not required |
| Foundry project + model, approved synthetic Search corpus, pinned agent | Required; use your own reviewed resources | Supplied synthetic fixtures |
| Service permissions and approved spending/data submission | Least-privilege invocation/query access; separate creation/upload rights for setup | No service permissions or service cost |
| Agent 365, Defender, Purview prerequisites | Only for the optional native-governance lab; separate licensing/consent/read access | Local simulations are explicitly not native evidence |

No presenter tenant, customer data, Node.js installation, or API key is required.
Use Entra authentication for Azure. Installing dependencies does not authorize
cloud calls, provisioning, publication, consent changes, or telemetry export.

### Prepare the shared Python environment

Bash and PowerShell:

```text
git clone https://github.com/honestypugh2/foundry-security-agent-accelerator.git
cd foundry-security-agent-accelerator
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
```

Already have the repository? Start at `uv sync`. This first doctor command is
local/configuration-only; it does not connect to Azure or establish Azure health.
`fsa` and `python -m fsa` use the same implementation.

In VS Code, open the repository folder and
[00 setup](notebooks/00_environment_setup.ipynb). Select **the repository's
`.venv` Python interpreter** as the notebook kernel, not an unrelated global
kernel. Run the setup cells in order. Then follow
[Azure configuration](#3-azure-live-workshop-setup) or the
[explicit local fallback](#4-local-fallback-when-azure-is-unavailable).

`demo` and `ask` display a clean, color-coded view in a terminal: cyan context,
green allowed/answered results, red denials, and amber quarantine or approval
boundaries. Decisions and citations come from the run, not a prerecorded transcript.
Local results are explicitly labeled synthetic. Azure uses the selected equipment
or four-function presentation profile; it never silently substitutes local results.
Redirected output stays JSON for scripts. Use `--format json` explicitly, or
`--format text --color always` to force the presentation view in captured output.
Use `--color never` or set `NO_COLOR` for plain text.

```bash
uv run python -m fsa demo --format text --color always
# Existing equipment compatibility profile:
uv run python -m fsa --mode azure demo --profile equipment --format text --color always
# Separate four-tool presentation profile, after reviewed setup and version pinning:
uv run python -m fsa --mode azure demo --profile presentation --authorize --format text --color always
```

See the [notebook guide](notebooks/README.md) for execution and consent rules.

### Reproducible SDK environment

The frozen [lockfile](uv.lock), not an unbounded install of `latest`, defines the
workshop environment. The direct Microsoft/Azure SDK release baseline is:

| SDK | Locked version | Official release reference |
|---|---|---|
| Azure AI Projects | 2.11.0 | [Release history](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md) |
| Azure Identity | 1.27.0 | [Release history](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/identity/azure-identity/CHANGELOG.md) |
| Azure AI Search | 12.1.0 | [Package](https://pypi.org/project/azure-search-documents/) |
| Azure AI Content Safety | 1.0.0 | [Package](https://pypi.org/project/azure-ai-contentsafety/) |
| Azure Monitor OpenTelemetry | 1.8.12 | [Package](https://pypi.org/project/azure-monitor-opentelemetry/) |
| Azure Monitor Query | 2.0.0 | [Release history](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/monitor/azure-monitor-query/CHANGELOG.md) |
| Azure AI Evaluation | 1.18.12 | [Release history](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/evaluation/azure-ai-evaluation/CHANGELOG.md) |

Upstream OpenTelemetry SDK and optional OTLP/HTTP exporter are both 1.45.2.
Stable package versions do not make every feature GA: some evaluation features
and Monitor's transitive exporters have separate preview/experimental maturity.
No Agent Framework, Agent 365, or deprecated observability SDK is added merely
to imply an integration. SDK updates do not upgrade your remote agent, grant
permissions, or establish live service compatibility.

## 2. Work through the labs

**Azure Live:** 00 -> Azure setup -> 01 -> 02 -> 03 -> 04; add 05 only when its
native-governance prerequisites are met.
**Local fallback:** 00 -> 06 for a consolidated walkthrough, or 00 -> 02 -> 03 -> 04
for the individual offline exercises.
Full instructions, costs and expected results are in the
[participant guide](docs/participant-lab/README.md).

| Lab | Learning outcome | Execution |
|---|---|---|
| [00 Setup](notebooks/00_environment_setup.ipynb) | Check Python, kernel and package | Local; no credentials |
| [01 Azure Live](notebooks/01_foundry_agent_live.ipynb) | Review separate profiles, configure or explicitly create dedicated tools/index, invoke the governed client | Azure path; own resources, permissions, consent and cost |
| [02 Protect](notebooks/02_protect_identity_and_tools.ipynb) | Inspect access boundaries, injection rejection and independent approval | Local by default; optional live section requires consent |
| [03 Prove](notebooks/03_prove_evaluations_and_redteam.ipynb) | Compare safe/unsafe gates and reconcile evidence; separately select the live six-scene regression | Local gates; live regression is default-off and billable |
| [04 Operate](notebooks/04_operate_traces_and_audit.ipynb) | Inspect traces and verify/tamper-test an audit copy; independently query approved Monitor ingestion | Local by default; Azure invocation/export/query need separate consent |
| [06 Consolidated local lab](notebooks/06_local_fallback.ipynb) | Run the end-to-end local scenarios and lifecycle simulation | Local; standalone after setup |
| [05 Agent 365](notebooks/05_agent365_extension.ipynb) | Separate settings, portal observations and attestations | Optional; independent licensing/permissions |
| [07 Request, approval, publication](notebooks/07_agent365_request_approval_publish.ipynb) | Review seven checks, reject maker self-approval, compare package-bounded access and retain v1 after rejecting v2 | Local model; optional read-only portal checklist, no native mutation |

Live notebook cells remain OFF by default even on the recommended Azure route.
Run them cell by cell, reviewing each scope and prompt. Choose **one** live
invocation exercise within the approved session budget rather than running every
example or retrying until PASS. If Azure fails, retain the failure and switch
explicitly to the fallback; no automatic downgrade is implemented.

Success means understanding the observed boundary, not making every check green.
Guest/HR denials, self-approval refusal and deliberate unsafe-gate exit **1** are
expected exercises. Run expected failures separately, not chained with `&&`.
All supplied writes produce **DRY_RUN receipts only**; no business system is changed.

The default local demo uses six fictional retention/ticket/injection/HR/approval
scenarios. The explicit Azure `--profile presentation --authorize` path runs the
same questions using a separately pinned Foundry agent with four client-side
function tools and a dedicated, approved synthetic Azure Search corpus.
Retention values are training fixtures, not legal advice. Other
questions retain the equipment workflow; select `--profile presentation` or
`--profile equipment` explicitly when comparing them. Synthetic identities and
approvers are not Entra/OBO or authenticated enterprise approvals.

Use [troubleshooting](docs/participant-lab/troubleshooting.md) for errors and
[cleanup](docs/participant-lab/cleanup.md) when finished. Keep generated `.fsa`
and `artifacts` private, and clear notebook outputs before sharing.

## Reference: governed equipment workflow

1. A trusted caller supplies subject and entitlements.
   Input screening runs before retrieval or model execution.
2. Retrieval uses Azure AI Search in Azure mode or original synthetic policy
   fixtures offline, with server-side entitlement trimming in Azure.
3. Retrieved text stays untrusted; injection signatures reject known attacks.
   Optional Azure AI Content Safety adds input/output content moderation.
4. An explicit read-only tool allowlist excludes the writer and delegation.
5. Local deterministic text or a real read-only Foundry prompt agent summarizes.
   The application requires approved-source citations or an exact abstention.
6. Application-authored proposal passes deterministic policy.
7. Exact, scoped, expiring, independently issued approval is checked.
8. The sole writer creates an idempotent SQLite DRY_RUN receipt.
9. Hash-linked audit and OTel spans preserve evidence of the run.

The model does not choose entitlements, approve proposals, dispatch arbitrary
tools, or control the writer. Signature detection is heuristic, not universal
prompt-injection prevention. See [security limitations](SECURITY.md).

## 3. Azure Live workshop setup

Read [the live lab](docs/participant-lab/azure-live-lab.md) before running cloud
commands. Authentication, cloud selection, subscription, model quota, region,
resource permissions and network reachability are your responsibility.
The existing-project path does not require provisioning a new environment.

1. Prepare the shared environment and complete notebook 00.
2. Create private `.env` only if absent, using the platform-specific instructions
   below. Edit it locally from [.env.example](.env.example); never paste its
   contents into chat, screenshots, notebooks, or Git.
3. Configure your authorized cloud/tenant/subscription, resource group/account,
   Foundry project endpoint and model, and synthetic Search endpoint/index.
   The presentation profile additionally needs its separate agent name, immutable
   version and index. Set optional moderation/monitoring only within your approved
   scope. See the [complete Azure lab](docs/participant-lab/azure-live-lab.md).
4. Sign in personally with Azure CLI and select your approved cloud/subscription
   privately. Never copy a presenter's resource identifiers or print tokens.
5. Run configuration/read-only checks; review unresolved capabilities rather
   than treating a credential, enabled setting, or preflight result as service
   success. Then review the dedicated four-tool profile below.

Bash:

```bash
test -e .env || cp .env.example .env
az login
uv run python -m fsa --mode azure doctor
uv run python -m fsa azure whoami
uv run python -m fsa azure preflight
```

PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
az login
uv run python -m fsa --mode azure doctor
uv run python -m fsa azure whoami
uv run python -m fsa azure preflight
```

Configure `.env` and cloud selection **before** the checks. Doctor validates
configuration only; whoami is a redacted CLI-selection report, not proof of the
SDK's effective identity. Preflight can exit nonzero for unknown capabilities.

Follow the Bash or PowerShell instructions in the live lab. Configure only
ignored private `.env`, authenticate yourself and explicitly authorize each
service-cost/data-submission step. The workshop's default path does not deploy.

No Azure provisioning, agent publishing, tenant changes, registry mutation,
or cleanup is performed automatically. Mutation commands require explicit
authorization. Read-only preflight cannot establish every permission, quota,
license, or network fact; unresolved checks stay unknown.

The default selected workload is a **prompt agent**, not a hosted agent.
Validate your own Search, Content Safety and pinned Foundry agent through the
authorized live lab. The governed request should stop at `AWAITING_APPROVAL`
without a writer call. Verify Monitor ingestion independently; ordinary Search
is not Foundry IQ, and IQ discovery does not validate retrieval.
Application success is not native Agent 365/Defender/Purview validation.
Azure Government configuration support does not prove Foundry or Agent 365
feature availability. GCC, GCC High and DoD are distinct from Azure clouds.

### Four-tool Azure presentation profile

The equipment agent remains a no-tools compatibility path. The presentation
profile deliberately uses a different agent and index; no implicit upgrade occurs.
Review the function schemas, original synthetic corpus, permissions, and cost first:

```bash
uv run python -m fsa azure presentation-review
# MUTATION: only after owner review; refuses existing agent/index names.
uv run python -m fsa azure presentation-setup --authorize
```

Pin the returned version as `FSA_PRESENTATION_AGENT_VERSION` in ignored private
configuration. Never print `.env`. Setup creates only the dedicated synthetic
index and agent version; it does not publish to Microsoft 365, change consent/RBAC,
or enable telemetry. Partial setup failures require owner inspection, not blind
reruns or automatic deletion.

```bash
uv run python -m fsa --mode azure ask "How long must elected officials' email be retained?" --as analyst --profile presentation --authorize
uv run python -m fsa --mode azure demo --profile presentation --authorize
uv run python -m fsa --mode azure audit verify
uv run python -m fsa --mode azure trace show S4
```

The portal should show `search_policies`, `get_policy_section`, `get_ticket_status`,
and `create_records_request` on the separate agent. A Toolbox is not required:
the application executes these functions, not the portal playground. Each request
is bounded to three model calls and six proposed tool calls; retries are disabled.
Unknown tools, invalid arguments, replayed call IDs, unauthorized sources and
unreviewed agent definitions fail closed. Search filters classifications before
ranking, and returned rows must exactly match the approved synthetic corpus.

The live service calls do **not** make role labels into Entra OBO. Independent
approval exercises still use the local, signed, 15-minute synthetic approval
queue; the only possible receipt is DRY_RUN. Production requires authenticated
requesters/approvers and a separate authorization design. A six-scenario PASS
does not validate Agent 365, Defender, Purview, IQ or Monitor ingestion.

## 4. Local fallback when Azure is unavailable

Use this route if you lack an Azure subscription, permissions, quota, network
access, budget, or a supported service. It is also suitable for disconnected
practice after dependency installation. No Azure credentials are acquired and
private dotenv/remote exporter settings are excluded from local execution.

```bash
uv run python -m fsa --mode local doctor
uv run python -m fsa --mode local demo
uv run python -m fsa --mode local eval --gate
```

Expected: six synthetic scenes, intentional access/injection denials, approval
boundaries, and a passing safe local regression gate. Start
[06 Local walkthrough](notebooks/06_local_fallback.ipynb), or use
[02 Protect](notebooks/02_protect_identity_and_tools.ipynb),
[03 Prove](notebooks/03_prove_evaluations_and_redteam.ipynb), and
[04 Operate](notebooks/04_operate_traces_and_audit.ipynb) with live cells OFF.
These results are not Azure, Agent 365, Defender, or Purview validation.
See [fallback commands and expected outputs](docs/participant-lab/local-fallback.md).

## 5. Optional Agent 365 and portal observation

```bash
make agent365-preflight
make agent365-status
make agent365-verify
```

Use the [extension lab](docs/participant-lab/agent365-extension.md) and
[integration architecture](docs/agent365/integration-architecture.md).
For the customer request-to-publication scenario, use
[Lab 07: policy-template lifecycle](docs/participant-lab/request-approval-publish.md)
and its [executable notebook](notebooks/07_agent365_request_approval_publish.ipynb).
It models the decision boundaries locally; it does not publish an agent or
enforce native Conditional Access/access packages.
Supported read-only resource settings are distinct from registry, ownership,
sponsorship, lifecycle and actual activity evidence. Unsupported API checks
use structured manual verification; missing evidence never becomes PASS.
An enabled `a365LoggingEnabled` flag alone is **not** proof of ingestion.
No Defender alerts, Purview events or Agent Registry entries are fabricated.

For an optional read-only Agent 365 and Defender portal walkthrough, follow the
[extension lab's observation checklist](docs/participant-lab/agent365-extension.md#optional-read-only-portal-observation).
Show only what is visible in your authorized environment. Portal observations
are separate from local simulations and repository validation; keep identifying
details and captures private.

Read-only Foundry availability inspection and saved-fixture rehearsal:

```bash
uv run fsa azure agent-status --from-json data/agent_state/blocked_new_agent.json
# Only against your authorized, configured Azure environment:
uv run fsa azure agent-status
```

Saved input always says offline / SIMULATED. Runtime, developer configuration and
Entra identity/blueprint states are interpreted independently, including legacy
exceptions. This is not a registry query. See the
[integration guide](docs/agent365/integration-architecture.md).

## Reference: evaluation and evidence

```bash
make test-security
make eval
uv run fsa gate path/to/normalized-evaluation-evidence.json
make operate-trace
uv run fsa redteam reconcile
# Expected exit 1 for the synthetic unsafe/unknown fixture:
uv run fsa redteam reconcile --strict
uv run fsa evidence
```

Azure-first evaluation and telemetry paths are implemented, not just optional
package declarations:

```bash
# Only after configuring Azure and explicitly authorizing service cost/data submission:
uv run fsa evaluate --mode azure --data data/evaluation/smoke.jsonl --output artifacts/eval-01 --authorize
# Read-only Application Insights / Log Analytics observation:
uv run fsa observe --correlation-id <printed-correlation-id>
```

See [Foundry evaluations](docs/evaluations/foundry-service.md) and
[Azure Monitor / OpenTelemetry](docs/observability/trace-architecture.md).
Azure judges report quality separately from security release. Local pytest-based
evaluations and upstream OTel JSON are explicit open-source fallbacks; standard
OTLP collector export is also available by configuration. No Azure service error
automatically switches to a fallback.

See [evaluation outcomes and gates](docs/evaluations/framework.md) and
[seven-layer reconciliation](docs/evaluations/redteam-reconciliation.md)
for schemas, strict semantics and raw-evidence retention.

`evaluate` runs synthetic regression cases: expected denials and missing-evidence
results are successful **regression tests**, not a production release PASS.
`gate` evaluates one normalized `EvaluationEvidence` contract and exits nonzero
unless its security outcome is PASS. CI also fails on failed deterministic
security tests. Unknown score polarity is never guessed. Raw evaluator records
and human adjudications are retained separately.

## Workshop reference material

### Reference architecture

![Foundry and Agent 365 six-plane reference](docs/assets/architecture/six-plane-reference.svg)

**[Open the interactive, animated six-plane diagram](docs/assets/architecture/six-plane-reference.html)**:
play/pause, step through the flow, or select a control plane for its evidence
boundary. Download/open the HTML locally; GitHub displays source rather than
running interactive HTML. The SVG above is a GIF-like animated preview, with
reduced-motion support. Neither animation makes service calls.

Explore the [editable Draw.io diagrams and implementation flow](docs/architecture/overview.md).
The diagrams distinguish the caller-side Python runtime from Azure services and
native governance evidence. They are workshop references, not deployment or
production-readiness attestations.

- [Documentation index](docs/README.md)
- [Technical portal](docs/index.html)
- [Participant Azure lab](docs/participant-lab/azure-live-lab.md)
- [Local fallback](docs/participant-lab/local-fallback.md)
- [Six-pillar control matrix](docs/security/six-pillar-control-matrix.md)
- [Agent 365 integration guide](docs/agent365/integration-architecture.md)
- [Security model and reporting](SECURITY.md)

Open the technical portal directly, or use `make docs`.
Core content is offline. Reference links require internet.

## Maintainers: validation and infrastructure

```bash
make setup
make validate
make dependency-scan
make sbom
```

`make validate` runs Ruff, format checks, strict Pyright, coverage-enforced
tests, security/evaluation regressions, local demo, Bicep compilation and a
conservative source-pattern scan. It does not deploy. Bicep compilation proves
syntax/types, not resource-provider acceptance or regional model availability.
See [deployment guidance](docs/architecture/azure-deployment.md) for what-if,
cost and cleanup. No broad delete is part of local validation.

GitHub Actions are pinned to full commit SHAs and have read-only repository
permissions. CI has no tenant credentials or automatic deployment. Protected
environment/OIDC deployment is documented but requires authorized setup.

## License and evidence boundaries

Original implementation: [MIT](LICENSE). See
[reuse and attribution](docs/reuse-and-attribution.md) for implementation references
and adapted patterns. Private build records and presenter materials are not
part of the workshop source.
Live Azure execution, Agent 365 ingestion, Defender/Purview signals and
government-cloud parity must be verified separately. Consult the status
and evidence guides rather than inferring readiness from a demo.
