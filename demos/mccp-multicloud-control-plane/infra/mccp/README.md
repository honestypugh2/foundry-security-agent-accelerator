# infra/mccp

## Will this touch my existing environment?

| Mode | What it creates | What it changes in the existing lab (`infra/live.bicep`) |
|---|---|---|
| **NEW** (default) | Foundry account + project + `gpt-5-mini` deployment, API Management gateway, Log Analytics + App Insights, kill-switch Logic App, action group, alert, budget — all in the resource group you choose | Nothing |
| **ATTACH** (`--attach-rg <lab-rg>`) | API Management gateway, Log Analytics + App Insights, kill-switch Logic App, action group, alert, budget in the resource group you choose | **One role assignment** on the lab's Foundry account (*Cognitive Services OpenAI User* for the gateway's managed identity). The account, project `security-project`, deployment `policy-model`, Search, Content Safety, workspace and role assignments are only read |

Resource names come from `uniqueString(<target resource group id>)`, so they never collide with the lab's `fsa-<suffix>` names. ARM deployments are incremental: nothing that is not in the template is deleted.
Deploy into its **own** resource group (default `rg-contoso-mccp`) so cleanup is one `az group delete` that leaves the lab alone. The lab's Log Analytics workspace has a 0.1 GB/day cap, which is why the gateway gets its own workspace: if ingestion stopped there, the automatic kill alert would stop too.

Deploying needs **Owner** (or Contributor + User Access Administrator) on the target resource group, and on the lab resource group in ATTACH mode, because the template creates role assignments.

## Deploy (WSL / Linux / macOS)

```bash
cd <repo>/demos/mccp-multicloud-control-plane          # run from the demo folder
az login --use-device-code && az account set -s <subscription>
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg> --what-if-only   # preview, deploys nothing
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg>                  # ATTACH
infra/mccp/deploy.sh --rg rg-contoso-mccp --location eastus2                          # NEW
```

`deploy.sh` runs, in order: CLI + sign-in check, resource provider registration, model/quota check (NEW) or lab lookup (ATTACH), `az bicep build` + `build-params`, `az deployment group validate`, `what-if`, confirmation, deployment, writes `.env.mccp.azure` in the demo folder (git-ignored; `python -m mccp` loads it), saves the smoke-test response to `artifacts/mccp/smoke-response.json`, and a smoke test through the gateway with your `az login` token (expects HTTP 200).

Parameters come from environment variables in `main.bicepparam` (no email, tenant or account name is committed). `deploy.sh` sets the main ones; others: `MCCP_MODEL_NAME`, `MCCP_MODEL_VERSION`, `MCCP_MODEL_CAPACITY`, `MCCP_TPM_PER_AGENT`, `MCCP_USER_MONTHLY_TOKENS`, `MCCP_BUDGET_USD`, `MCCP_KILL_TOKENS_PER_HOUR`, `MCCP_APIM_SKU`.

## Files

| File | Purpose |
|---|---|
| `main.bicep` | NEW/ATTACH switch, modules, outputs (the `.env` values) |
| `main.bicepparam` | Parameters from environment variables |
| `deploy.sh` | Preflight → build → validate → what-if → deploy → `.env.mccp.azure` → smoke test |
| `modules/monitoring.bicep` | Log Analytics + workspace-based Application Insights for the gateway |
| `modules/foundry.bicep` | NEW: `AIServices` account (`allowProjectManagement`, `disableLocalAuth`), `gpt-5-mini` GlobalStandard deployment `policy-model`, project, diagnostics |
| `modules/foundry-existing.bicep` | ATTACH: read-only lookup of account, project and deployment (fails fast if any is missing) |
| `modules/foundry-access.bicep` | The one role assignment: gateway managed identity → *Cognitive Services OpenAI User* on the account |
| `modules/apim.bicep` | APIM (default `BasicV2`, system MI), named values, Foundry backend, API `ai/openai` + policy, App Insights logger + diagnostics, product `agents` + two agent subscriptions |
| `modules/killswitch.bicep` | Logic App (MI, *API Management Service Contributor* on this APIM only), action group, scheduled query alert per agent, RG budget 80%/100%/forecast |
| `policies/ai-gateway.xml` | Gateway policy (mirrored by `src/mccp/policy_sim.py`) |
| `kql/*.kql` | Token usage, MTD spend, stopped calls, alert query |

## Identity at the gateway: Entra (default) or Okta

`policies/ai-gateway.xml` holds two `validate-jwt` blocks between markers. `apim.bicep` turns the one you did not choose into an XML comment at deploy time.

* **entra** (default): accepts tokens from your tenant for audience `https://cognitiveservices.azure.com`, so `az account get-access-token --resource https://cognitiveservices.azure.com` (or `DefaultAzureCredential`) works with no app registration. Both v1 (`sts.windows.net`) and v2 issuers are listed. In production, register an API (`api://...`) and set `MCCP_ENTRA_AUDIENCE`.
* **okta**: `deploy.sh --okta` with `OKTA_ISSUER` and `OKTA_AUDIENCE` exported; `python -m mccp call` then uses Okta client credentials.

## Model

NEW mode deploys `gpt-5-mini` `2025-08-07` (GA; the same model the base repo's lab uses). The earlier default, `gpt-4.1-mini` `2025-04-14`, is listed as deprecated on the [Foundry model retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule) with retirement on 2027-04-14. gpt-5 family models take `max_completion_tokens` (not `max_tokens`) and count reasoning tokens against it; the client sends `reasoning_effort: minimal` (`MCCP_REASONING_EFFORT`).

## Verified against Microsoft Learn

* `llm-token-limit`: 429 when tokens-per-minute is exceeded, 403 when the quota is exceeded; "can be used multiple times per policy definition"; applies to classic and v2 gateways; v2 uses a token bucket.
* Named values: value "may not be empty" (hence the `none` sentinel) and "will not be filled on 'GET' operations", so the Logic App and `killswitch.py` read it with `POST …/namedValues/{name}/listValue`.
* Subscriptions: `scope` format `/products/{productId}`.
* Logger: Application Insights logger credential is the instrumentation key.

## Still check on first deployment

* App Insights → *Usage and estimated costs* → *Custom metrics* → enable alerting on custom metric dimensions (the kill alert splits by `agent`). `deploy.sh` reminds you.
* How long a named-value change takes to reach the gateway (seconds in practice; measure it once).
* The `scheduledQueryRules@2023-03-15-preview` schema in your cloud (`az deployment group validate` covers this).

## Troubleshooting

* `ServiceAlreadyExistsInSoftDeletedState` / custom domain in use after a delete: `az apim deletedservice purge --service-name <name> --location <loc>` and `az cognitiveservices account purge -g <rg> -n <account> -l <loc>`.
* `InsufficientQuota` (NEW): lower `MCCP_MODEL_CAPACITY` or use `--attach-rg`.
* Smoke test 401: the token audience or tenant does not match `entra-audience` / `entra-tenant-id`. 500 with `gateway_error`: the role assignment may still be propagating; wait a few minutes.

## Cleanup
```bash
az group delete -n rg-contoso-mccp --yes --no-wait
az apim deletedservice purge --service-name <apim-name> --location <loc>          # APIM soft-delete
az cognitiveservices account purge -g rg-contoso-mccp -n <account> -l <loc>       # NEW mode only
```
In ATTACH mode the lab's Foundry account keeps one orphaned role assignment for the deleted gateway identity; remove it in the portal (Access control → Role assignments) if you want it gone.
