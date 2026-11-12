# Workshop participant guide

Use your own authorized tenant; no presenter or customer tenant dependency.
**Start locally.** Python 3.12, uv and Git are required; VS Code Python/Jupyter
extensions are needed only for notebooks. Install dependencies from the
repository root. Core labs require no Azure account or service connection.

## Lab order and expected outcomes

1. [00 Setup](../../notebooks/00_environment_setup.ipynb): select `.venv`;
   local checks pass and Azure remains NOT_CHECKED.
2. [02 Protect](../../notebooks/02_protect_identity_and_tools.ipynb): observe
   allowed requests, denied injection/access and independent DRY_RUN approval.
3. [03 Prove](../../notebooks/03_prove_evaluations_and_redteam.ipynb): safe gate
   passes; intentionally unsafe sandbox fails. Neither result certifies production.
4. [04 Operate](../../notebooks/04_operate_traces_and_audit.ipynb): inspect
   retained local spans; verify original audit and reject a tampered copy.

Alternative: after setup, use [06 consolidated local lab](../../notebooks/06_local_fallback.ipynb).
Then choose optional Azure/Agent 365 extensions if you have the prerequisites.
Use the [notebook execution guide](../../notebooks/README.md) before running cells.

## Choose an extension or alternative

| Path | Duration / level | Dependencies / cost | Guide |
|---|---|---|---|
| A: Azure Live | 20-45 min / L300-L400 | Existing project/model/no-tools pinned prompt agent, synthetic Search index, authorized data-plane access; inference/Search/moderation/monitoring may be billable | [Azure](azure-live-lab.md), [notebook 01](../../notebooks/01_foundry_agent_live.ipynb) |
| B: Local Fallback | 20 min / L200-L400 | Installed Python dependencies only; no Azure credentials, license or service cost | [Local](local-fallback.md), [notebook 06](../../notebooks/06_local_fallback.ipynb) |
| C: Agent 365 optional | 20+ min / L300-L400 | Separately verified supported tenant/cloud, licensing, consent and least-privilege read permissions | [Extension](agent365-extension.md), [notebook 05](../../notebooks/05_agent365_extension.ipynb) |
| No-code observation | 15 min / L200-L300 | Browser and existing offline HTML; no service calls | [No-code](no-code-security-observation.md) |

## Setup: Bash

```bash
uv sync --frozen --all-extras --dev
source .venv/bin/activate
python -m fsa doctor
python -m fsa ask "Explain synthetic equipment policy." --as analyst
python -m fsa eval --gate
```

## Setup: PowerShell

```powershell
uv sync --frozen --all-extras --dev
.\.venv\Scripts\Activate.ps1
python -m fsa doctor
python -m fsa ask "Explain synthetic equipment policy." --as analyst
python -m fsa eval --gate
```

If activation is restricted, use `uv run python -m fsa ...` instead; no execution
policy changes required. In VS Code select `.venv` as the Python/Jupyter kernel.
Run notebook cells top to bottom. Restart the kernel before repeating a lab.
For local labs use Run All; in notebook 02 the live branch stays off by default.
Notebooks 01/05 have interactive authorization prompts: run them cell by cell,
not as an unattended batch.

Install dependencies once before disconnecting. Local runs ignore private dotenv
and remote exporter settings. Synthetic roles/approvals are not Entra/OBO or
enterprise human authorization. All supplied writing is DRY_RUN.
Cloud notebook cells require deliberate confirmation and are never run in PR CI.
Clear all outputs before sharing.

Notebook 02 has an additional OFF-by-default Azure Search/moderation branch; CI
executes only its local/default path under network denial. Notebook 01 uses the
bounded end-to-end live validator. See the [dated real-service results](../APEX_AZURE_LIVE_RESULTS.md)
and [locally staged story data](../../data/synthetic/demo-search-documents.json).
Ordinary Search is not Foundry IQ; no IQ knowledge base was found in the tested environment.

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
