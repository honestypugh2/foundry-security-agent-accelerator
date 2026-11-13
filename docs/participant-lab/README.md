# Workshop participant guide

Use your own authorized tenant; no presenter or customer tenant dependency.
**Recommended: Azure Live, with an explicit local fallback.** Python 3.12, uv and
Git are required; VS Code Python/Jupyter extensions are needed for notebooks.
Install dependencies from the repository root. Start with the
[prerequisites matrix](../../README.md#1-prerequisites-and-workshop-setup).
Azure requires approved resources, supported services, permissions and budget;
the fallback requires none of those cloud prerequisites.

## Lab order and expected outcomes

1. [00 Setup](../../notebooks/00_environment_setup.ipynb): select `.venv`;
   local checks pass and Azure remains NOT_CHECKED.
2. [Azure setup](azure-live-lab.md), then
   [01 Azure Live](../../notebooks/01_foundry_agent_live.ipynb): review the
   dedicated four-function profile, pin the approved agent version, and select
   an authorized invocation. Existing approved resources need no recreation.
3. [02 Protect](../../notebooks/02_protect_identity_and_tools.ipynb): observe
   allowed requests, denied injection/access and independent DRY_RUN approval.
   The live presentation branch is a separate, default-off exercise.
4. [03 Prove](../../notebooks/03_prove_evaluations_and_redteam.ipynb): safe local
   gate passes; intentionally unsafe local sandbox fails. Select the live
   six-scene regression only within the shared budget. Neither certifies production.
5. [04 Operate](../../notebooks/04_operate_traces_and_audit.ipynb): inspect
   retained spans; verify original audit and reject a tampered copy. Separately
   authorize Monitor query/export and verify actual ingestion.
6. Optional [05 Agent 365](../../notebooks/05_agent365_extension.ipynb):
   observe native registry/activity/Defender/Purview evidence independently.
7. [07 Request, approval and publication](../../notebooks/07_agent365_request_approval_publish.ipynb):
   model the policy-template lifecycle locally, with package-bounded reads,
   rejected self-approval/unsafe update and retained v1. Native observation is an
   optional read-only checklist; no native publication or policy change runs.

**Azure unavailable:** after setup, use
[06 consolidated local lab](../../notebooks/06_local_fallback.ipynb), or run
02 -> 03 -> 04 with live cells OFF. No cloud error becomes a local PASS.
Use the [notebook execution guide](../../notebooks/README.md) before running cells.

## Choose your workshop path

| Path | Duration / level | Dependencies / cost | Guide |
|---|---|---|---|
| A: Azure Live (recommended) | Setup 20-45 min, then selected labs / L300-L400 | Existing project/model, reviewed dedicated four-function pinned agent and synthetic index, authorized data-plane access; separate setup rights if creating resources; service usage may be billable | [Azure](azure-live-lab.md), [notebook 01](../../notebooks/01_foundry_agent_live.ipynb) |
| B: Local Fallback | 20 min / L200-L400 | Installed Python dependencies only; no Azure credentials, license or service cost | [Local](local-fallback.md), [notebook 06](../../notebooks/06_local_fallback.ipynb) |
| C: Agent 365 optional | 20+ min / L300-L400 | Separately verified supported tenant/cloud, licensing, consent and least-privilege read permissions | [Extension](agent365-extension.md), [notebook 05](../../notebooks/05_agent365_extension.ipynb) |
| D: Policy-template lifecycle | 25-35 min / L300 | Local model needs no cloud credentials/cost; existing native observation requires separate read authorization | [Lab](request-approval-publish.md), [notebook 07](../../notebooks/07_agent365_request_approval_publish.ipynb) |
| No-code observation | 15 min / L200-L300 | Browser and existing offline HTML; no service calls | [No-code](no-code-security-observation.md) |

## Setup: Bash

```bash
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
```

## Setup: PowerShell

```powershell
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
```

No shell activation or execution-policy change is required. Doctor at this stage
is a local configuration check, not an Azure health check. Next follow the
[Azure setup](azure-live-lab.md) or the [fallback](local-fallback.md).
In VS Code select `.venv` as the Python/Jupyter kernel.
Run notebook cells top to bottom. Restart the kernel before repeating a lab.
For local labs use Run All with all live branches OFF.
For any live exercise, including 01/05, run cell by cell rather than as an
unattended batch. Reserve one session-wide model budget; running all live
examples is not the recommended workshop path.

Install dependencies once before disconnecting. Local runs ignore private dotenv
and remote exporter settings. Synthetic roles/approvals are not Entra/OBO or
enterprise human authorization. All supplied writing is DRY_RUN.
Cloud notebook cells require deliberate confirmation and are never run in PR CI.
Clear all outputs before sharing.

Notebook 02 has an additional OFF-by-default Azure Search/moderation branch; CI
executes only its local/default path under network denial. Notebook 01 has separate equipment-compatibility and dedicated four-function
presentation exercises. Use the latter for the Azure workshop. Configure your own authorized environment
using the [Azure lab](azure-live-lab.md).
[Locally staged story data](../../data/synthetic/demo-search-documents.json)
is not automatically uploaded. Ordinary Search is not Foundry IQ; independently
verify knowledge-base configuration and retrieval before claiming IQ success.

See [troubleshooting](troubleshooting.md), [cleanup](cleanup.md), and the
[local exercise commands](local-fallback.md).

## Production and Well-Architected Framework (WAF) disclaimer

This is an **educational workshop accelerator, not a production-ready solution**,
a Microsoft certification, compliance attestation, penetration test or completed
[Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
assessment. Local tests and compiled Bicep do not establish production readiness.

Before any production use, independently assess the WAF pillars: Reliability,
Security, Cost Optimization, Operational Excellence and Performance Efficiency.
Review threat models, authenticated identity/approval, private networking/egress,
data protection, monitoring and incident response, resilience/recovery, load,
quotas, costs and deployment/change controls with the responsible owners.
The teaching infrastructure is not private-network hardened.

If WAF means **Web Application Firewall**, this repository does not establish
its deployment, configuration or effectiveness. Application injection checks are
not a Web Application Firewall or a substitute for perimeter controls.

All supplied writers remain DRY_RUN. Local synthetic lifecycle/role/approval
output is not native Agent 365, Entra, Defender or Purview evidence. Cloud
extensions require separate authorization and verification in your environment.
