![Microsoft Foundry + Security + Agent 365 — Protect. Prove. Operate. Enterprise AI Agents.](docs/assets/readme-banner.png)

# Foundry + Security + Agent 365 Workshop

**Protect. Prove. Operate.** Hands-on Python labs for a governed agent workflow.
Start locally without Azure credentials; use your own authorized environment
for the optional Azure and Agent 365 labs.

> Azure governs the infrastructure. Foundry governs the AI workload.
> Agent 365 governs the deployed agent. Report centrally. Enforce natively.

This repository contains original synthetic examples. There is no presenter
tenant dependency. Local execution is not Azure validation, and application
telemetry is not Agent 365 activity-ingestion evidence.

> **Workshop, not production:** this accelerator is not production-ready,
> a security/compliance certification, or an Azure Well-Architected Framework
> (WAF) assessment. See the [production disclaimer](docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).

## 1. Set up and run the local quickstart

Prerequisites: **Python 3.12**, [uv](https://docs.astral.sh/uv/getting-started/installation/),
and Git. For notebooks, install the VS Code Python and Jupyter extensions.
No Node.js, Azure tenant or paid product license is needed for the local labs.
Dependency installation needs package access once; local exercises then run
without service access.

Bash and PowerShell:

```text
git clone https://github.com/honestypugh2/foundry-security-agent-accelerator.git
cd foundry-security-agent-accelerator
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
uv run python -m fsa demo
uv run python -m fsa eval --gate
```

Already have the repository? Start at `uv sync`. Expected: doctor reports
local/configuration-only, the six-scene synthetic demo reports PASS, and the
safe evaluation gate passes. These are local results, not Azure health checks.
`fsa` and `python -m fsa` use the same implementation.

In VS Code, open the repository folder, open
[00 setup](notebooks/00_environment_setup.ipynb), and select the repository's
`.venv` Python interpreter as the notebook kernel. Run cells from top to bottom.
See the [notebook guide](notebooks/README.md) for execution and consent rules.

## 2. Work through the labs

Core order: **00 -> 02 -> 03 -> 04**. Notebook 06 is an alternative consolidated
local walkthrough. Notebooks 01 and 05 are optional extensions, not prerequisites.
Choose labs to fit your session; full instructions, costs and expected results
are in the [participant guide](docs/participant-lab/README.md).

| Lab | Learning outcome | Execution |
|---|---|---|
| [00 Setup](notebooks/00_environment_setup.ipynb) | Check Python, kernel and package | Local; no credentials |
| [02 Protect](notebooks/02_protect_identity_and_tools.ipynb) | Inspect access boundaries, injection rejection and independent approval | Local by default; optional live section requires consent |
| [03 Prove](notebooks/03_prove_evaluations_and_redteam.ipynb) | Compare safe/unsafe gates and reconcile evidence | Local |
| [04 Operate](notebooks/04_operate_traces_and_audit.ipynb) | Inspect traces and verify/tamper-test an audit copy | Local |
| [06 Consolidated local lab](notebooks/06_local_fallback.ipynb) | Run the end-to-end local scenarios and lifecycle simulation | Local; standalone after setup |
| [01 Azure Live](notebooks/01_foundry_agent_live.ipynb) | Exercise existing Search, moderation and pinned Foundry agent | Optional; own resources, permissions, consent and cost |
| [05 Agent 365](notebooks/05_agent365_extension.ipynb) | Separate settings, portal observations and attestations | Optional; independent licensing/permissions |

Success means understanding the observed boundary, not making every check green.
Guest/HR denials, self-approval refusal and deliberate unsafe-gate exit **1** are
expected exercises. Run expected failures separately, not chained with `&&`.
All supplied writes produce **DRY_RUN receipts only**; no business system is changed.

The default local demo uses six fictional retention/ticket/injection/HR/approval
scenarios. Retention values are training fixtures, not legal advice. Other
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

## 3. Optional Azure extension

Read [the live lab](docs/participant-lab/azure-live-lab.md) before running cloud
commands. Authentication, cloud selection, subscription, model quota, region,
resource permissions and network reachability are your responsibility.
The existing-project path does not require provisioning a new environment.

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

## 4. Optional Agent 365 and portal observation

```bash
make agent365-preflight
make agent365-status
make agent365-verify
```

Use the [extension lab](docs/participant-lab/agent365-extension.md) and
[integration architecture](docs/agent365/integration-architecture.md).
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
