# mccp end-to-end plan

## 0. Outcomes (what the customer asked for)
1. **One inventory**: every agent across Azure, AWS and SaaS in one schema, with ServiceNow as the system of record.
2. **Agents managed like teammates**: each agent has an identity (Okta or Entra Agent ID), an owner, a cost center, and regular access reviews.
3. **Monthly dollar limits per user, with approval for more**: the APIM gateway enforces a user quota, and an approved user moves to a larger quota tier.
4. **A kill switch that actually stops agents**: it covers agent, user and global scopes, applies changes gateway → identity → record, and writes a receipt for every step.

## 1. Prerequisites
| Item | Notes |
|---|---|
| Azure subscription + resource group | Owner or (Contributor + User Access Administrator) to create role assignments |
| Model quota | NEW mode: GlobalStandard quota for `gpt-5-mini` 2025-08-07 in the target region (`deploy.sh` checks it). ATTACH mode: reuses the lab's `policy-model` deployment |
| Azure CLI ≥ 2.60 with Bicep | `az bicep install`; `az login` |
| Python 3.10+ (3.12 recommended) + uv | This folder has its own `pyproject.toml`; the local demo needs stdlib only |
| VS Code | Extensions: Python, Jupyter, Bicep, Azure Account (optional: REST Client) |
| Okta org (live mode) | Custom authorization server, scope `ai.gateway.invoke`, one API Services app per agent (public key / private_key_jwt), optional custom claim `agent_id` |
| ServiceNow instance (live mode) | Integration user with Table API access. **Confirm the AI Control Tower table/API with the ServiceNow team.** The default `x_ai_agent_registry` is a placeholder |
| Datadog (live mode) | API key, site, a webhook integration named `mccp-killswitch` |
| AWS (optional) | Credentials allowed to call `bedrock-agent:ListAgents`, `bedrock-agentcore-control:ListAgentRuntimes` (VALIDATE), and `iam:PutRolePolicy`/`DeleteRolePolicy` on the agent roles |

## 2. Set up in VS Code
1. In your clone of `foundry-security-agent-accelerator`: `git checkout -b feature/multicloud-control-plane`.
2. Unzip into a new folder: `mkdir -p demos/mccp-multicloud-control-plane && unzip -o <path-to>/mccp-multicloud-control-plane-addon.zip -d demos/mccp-multicloud-control-plane`, then `cd demos/mccp-multicloud-control-plane`. Every command below runs from this folder.
3. Run `uv sync` (this folder's own `pyproject.toml` and `.venv`; the base repo is not touched). Add extras with `uv sync --extra azure --extra aws --extra okta --extra notebooks` when you need them.
4. Run `uv run python -m mccp demo --mode local --color`. A colour terminal is recommended.
5. Open `notebooks/mccp/*.ipynb` and select this folder's `.venv` as the kernel. Keep `RUN_LIVE = False` until you deploy.
6. Run the tests with `uv run pytest -q`.
7. For live mode, copy `.env.example` to `.env` in this folder (git-ignored).

## 3. Deploy to Azure
```bash
az login --use-device-code && az account set -s <subscription>
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg> --what-if-only   # compile, validate, what-if only
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg>                  # ATTACH: reuse the lab's Foundry account
infra/mccp/deploy.sh --rg rg-contoso-mccp --location eastus2                          # NEW: own Foundry account + gpt-5-mini
```
`deploy.sh` writes the outputs to `.env.mccp.azure` in this folder (git-ignored, loaded automatically) and ends with an HTTP 200 smoke test through the gateway (response saved to `artifacts/mccp/smoke-response.json`).
APIM v2 tiers usually provision in minutes. Classic tiers can take 30–45 minutes.

## 4. Azure portal steps
1. **APIM → APIs → AI gateway (mccp) → Test**: call `chat-completions` with a valid Okta token. Expect 200 and the `x-remaining-tokens` header.
2. **APIM → APIs → Settings → Azure Monitor**: confirm that metrics are on. Turn on LLM message logging **only** if approved, because prompts may contain PHI.
3. **APIM → Named values**: confirm `killswitch-global=false`, `killed-agents=none`, `killed-users=none` and `quota-tier2-users=none`.
4. **Application Insights → Usage and estimated costs → Custom metrics**: turn on *with dimensions* (VALIDATE), so that `customMetrics` carries `agent-id` and the other dimensions.
5. **Foundry portal → Operate (Control Plane)**: review agents, models and assets for the project. Identify the stop/block action you will show (VALIDATE blade names).
6. **Entra admin center → Agent ID**: confirm agent identities for the Foundry and Copilot Studio agents (VALIDATE tenant availability).
7. **Logic App → Run trigger** with the payload from `python -m mccp alert-payload --agent contoso-rev-cycle-coder`, then check `killed-agents`. Remove the agent again with `python -m mccp revive --mode azure --agent contoso-rev-cycle-coder --authorize`.
8. **Cost Management → Budgets**: `mccp-monthly-budget` with notifications at 80% actual, 100% actual and 100% forecast.

## 5. Okta / ServiceNow / Datadog wiring
* **Okta**: for each agent, create an API Services app and register its public key. Set access-token lifetime to 5–15 minutes. If you use the claim, add `agent_id` to the token. Put the app id in the `okta_app_id` registry field. Lifecycle kill calls `POST /api/v1/apps/{id}/lifecycle/deactivate` and needs an API token or OAuth with `okta.apps.manage`.
* **ServiceNow**: confirm the table and columns (the `u_*` names are placeholders). Run `python -m mccp sync-servicenow --mode azure`, which writes DRY_RUN receipts; review the payloads, then rerun with `--authorize`.
* **Datadog**: run the OTel Collector with `otel/collector-config.yaml`. Create the webhook integration with the Logic App callback URL, which is a secret. Then create the monitor from `datadog/monitor_token_budget.json` after removing `_notes`.

## 6. Run order (live)
1. `inventory --mode azure`: check the warnings.
2. `sync-servicenow --mode azure`: review, then `--authorize`.
3. `call --mode azure --agent contoso-claims-triage`: expect 200.
4. `spend --mode azure --scope user`
5. `kill --mode azure --agent contoso-rev-cycle-coder`: DRY_RUN, review the receipts.
6. `kill --mode azure --agent contoso-rev-cycle-coder --authorize`, then `call`, which should return 423 once the named value reaches the gateway.
7. `revive --mode azure --agent contoso-rev-cycle-coder --authorize`

## 7. Rollback / cleanup
* Revive any killed agent, user or global scope: `python -m mccp revive --mode azure --agent X --authorize` (or `--user`, `--global`).
* Reactivate Okta apps if you deactivated them by hand: `POST /api/v1/apps/{id}/lifecycle/activate`.
* Delete everything: `az group delete -n rg-contoso-mccp --yes --no-wait`.
* APIM uses soft-delete. If you will reuse the name, purge it: `az apim deletedservice purge --service-name <name> --location <region>`.
* Cognitive Services accounts also soft-delete. Purge with `az cognitiveservices account purge -g <rg> -n <name> -l <region>`.
* Local: `rm -rf artifacts/mccp`.

## 8. Cost (ILLUSTRATIVE; check the Azure pricing calculator)
| Resource | Driver | Demo-scale estimate |
|---|---|---|
| APIM BasicV2 | hourly unit price | the largest fixed cost; delete after the demo |
| Foundry model (GlobalStandard) | tokens consumed | cents for the demo |
| Log Analytics / App Insights | GB ingested | low for a demo (30-day retention) |
| Logic App (Consumption) | per action execution | negligible |
| Budget / alerts | scheduled query rule per evaluation | low |
Budget guardrail: `budgetAmount` (default $500/month) with 80/100% notifications.
