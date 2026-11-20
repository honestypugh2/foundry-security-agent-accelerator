# BUILD_REPORT: mccp multi-cloud AI control plane add-on

Built offline for the Contoso Health (synthetic) demo on 2026-11-20. Uses only the Python standard library in local mode.

## File tree (63 files, unzipped into `demos/mccp-multicloud-control-plane/`)
```
.env.example
.gitignore
BUILD_REPORT.md
Makefile
README.md
data/mccp/agents.json
data/mccp/budgets.json
data/mccp/prices.json
data/mccp/usage_fixture.jsonl
datadog/monitor_token_budget.json
datadog/webhook_payload.json
docs/mccp/ARCHITECTURE.md
docs/mccp/DEMO_RUNBOOK.md
docs/mccp/PLAN.md
infra/mccp/README.md
infra/mccp/deploy.sh
infra/mccp/kql/budget_breach_alert.kql
infra/mccp/kql/killed_calls.kql
infra/mccp/kql/spend_month_to_date.kql
infra/mccp/kql/token_usage_by_agent.kql
infra/mccp/main.bicep
infra/mccp/main.bicepparam
infra/mccp/modules/apim.bicep
infra/mccp/modules/foundry-access.bicep
infra/mccp/modules/foundry-existing.bicep
infra/mccp/modules/foundry.bicep
infra/mccp/modules/killswitch.bicep
infra/mccp/modules/monitoring.bicep
infra/mccp/policies/ai-gateway.xml
mccp/README.md
notebooks/mccp/01_inventory_registry.ipynb
notebooks/mccp/02_gateway_token_limits.ipynb
notebooks/mccp/03_observability_otel_datadog.ipynb
notebooks/mccp/04_finops_spend_forecast.ipynb
notebooks/mccp/05_kill_switch_drill.ipynb
notebooks/mccp/06_end_to_end_local.ipynb
otel/collector-config.yaml
pyproject.toml
src/mccp/__init__.py
src/mccp/__main__.py
src/mccp/cli.py
src/mccp/config.py
src/mccp/demo.py
src/mccp/finops.py
src/mccp/gateway.py
src/mccp/killswitch.py
src/mccp/models.py
src/mccp/okta.py
src/mccp/policy_sim.py
src/mccp/receipts.py
src/mccp/registry.py
src/mccp/report.py
src/mccp/servicenow.py
src/mccp/telemetry.py
tests/mccp/_mccp_helpers.py
tests/mccp/test_cli_demo.py
tests/mccp/test_demo_layout.py
tests/mccp/test_finops.py
tests/mccp/test_infra_static.py
tests/mccp/test_killswitch.py
tests/mccp/test_live_client.py
tests/mccp/test_policy_sim.py
tests/mccp/test_registry.py
```

## Environment checks
| Check | Result |
|---|---|
| Python | 3.12 |
| `pytest` importable | **No**. Tests are `unittest.TestCase` classes, so they also run under pytest |
| `bicep` / `az bicep` CLI | **Not available**: Bicep was **not compiled** |
| Internet / package installs | None (stdlib only; azure/otel/boto3/pyjwt imports are guarded) |

## Executed and passed
| What | Command | Result |
|---|---|---|
| Unit + integration tests | `python -m unittest discover -s tests/mccp -p "test_*.py"` | **Ran 39 tests in 5.922s → OK** (39 tests) |
| End-to-end demo | `uv run python -m mccp demo --mode local` (or `PYTHONPATH=src python3 -m mccp demo --mode local`) | exit 0, 172 lines, 12 scenes, deterministic (asserted by a test) |
| CLI smoke | `inventory`, `spend --scope cost_center`, `kill`/`revive` (agent, user, global, `--hard`), `call`, `approve`, `policy-map`, `--mode azure` without config | all behaved as designed: azure mode without config fails with a clear message and makes no calls |
| Notebooks | executed every code cell of all 6 notebooks with `RUN_LIVE=False` (plain `exec`, no Jupyter) | all OK |
| Byte-compile | `python -m compileall src tests` | OK |
| Policy mapping | `python -m mccp policy-map` (every XML element has a simulator function) | OK |

## Not executed or not validated
* **Azure**: no deployment, `what-if` or ARM calls. Bicep (`main.bicep` + 4 modules) is **not compiled**. Run `az bicep build` first.
* **APIM policy** (`ai-gateway.xml`): not loaded into a real APIM. Uses only documented elements (`validate-jwt`/`openid-config`, `set-variable`, `choose/when`, `return-response`, `llm-token-limit`, `llm-emit-token-metric`, `authentication-managed-identity`, `set-backend-service`, `set-header`). Items to check are marked VALIDATE: multiple or nested `llm-token-limit`, the empty-named-value sentinel `none`, the quota status code (403 per the docs; TPM = 429), and the counting window.
* **Okta**: no token, introspection or lifecycle calls. `private_key_jwt` needs `pyjwt[crypto]`, which is not installed.
* **ServiceNow**: no Table API calls. The table `x_ai_agent_registry` and the `u_*` columns are placeholders; confirm the AI Control Tower table/API.
* **Datadog / OTel Collector**: configs not loaded. The Datadog metric name for the OTel histogram is VALIDATE.
* **Foundry SDK / Bedrock / AgentCore adapters**: SDKs not installed; code paths compiled but not executed. AgentCore `list_agent_runtimes` is VALIDATE.
* **Logic App** workflow expressions: not run.
* **ruff**: not available, not run.

## Deviations from the spec (intentional)
* ARM api-version for named values and subscriptions is **2024-05-01** (per the build brief; the spec mentioned 2024-06-01-preview). It can be overridden with `APIM_ARM_API_VERSION`.
* The runaway story shows **429** (tokens-per-minute) **and then 403** (monthly token quota), because the APIM docs give 403 for an exhausted `token-quota`. The spec's single "429" was split to match the documented behaviour.
* Additions: a `killed-users` named value (user-scope kill), `quota-tier2-users` (approval for more), `data/mccp/budgets.json`, `src/mccp/receipts.py`, and `tests/mccp/_mccp_helpers.py`. `tests/mccp` has no `__init__.py` so it can't clash with the `mccp` package.
* `kill --hard` also suspends the APIM subscription. The simulator models the built-in subscription check, which runs before policies and returns 401. The default (soft) kill returns the clearer 423.

## Demo output (first 80 lines, `NO_COLOR=1`)
```

══════════════════════════════════════════════════════════════════════════════
 SCENE 01 │ Contoso Health · Multi-cloud AI agent control plane
          │ mode=local · SIMULATED · demo clock 2026-11-20 09:00 UTC
══════════════════════════════════════════════════════════════════════════════
  ▸ Registry / system of record ... ServiceNow AI Control Tower
  ▸ Agent identity ................ Okta (one service app per agent) + Entra Agent ID for Microsoft agents
  ▸ Runtime enforcement ........... Azure API Management AI gateway (validate-jwt, llm-token-limit, kill lists)
  ▸ Agent platform & control ...... Microsoft Foundry Control Plane (+ AWS Bedrock/AgentCore, Copilot Studio, Snowflake Cortex)
  ▸ Observability ................. OpenTelemetry GenAI → Azure Monitor + Datadog

══════════════════════════════════════════════════════════════════════════════
 SCENE 02 │ One inventory: every agent, every cloud
          │ single source of truth, merged from platform adapters
══════════════════════════════════════════════════════════════════════════════
  ┌────────────────────────────┬──────────────────┬───────┬─────────────┬──────────────────┬─────────┬───────────┬───────────────┐
  │ agent                      │ platform         │ cloud │ owner       │ okta app         │ gateway │ budget/mo │ access review │
  ├────────────────────────────┼──────────────────┼───────┼─────────────┼──────────────────┼─────────┼───────────┼───────────────┤
  │ contoso-claims-triage      │ foundry          │ azure │ maria.gomez │ 0oaSIMclaims0001 │ yes     │ $150      │ 49d ago       │
  │ contoso-rev-cycle-coder    │ foundry          │ azure │ j.chen      │ 0oaSIMrevcyc0002 │ yes     │ $60       │ 98d ago ⚠     │
  │ contoso-patient-scheduling │ bedrock          │ aws   │ r.silva     │ 0oaSIMsched00003 │ yes     │ $45       │ 30d ago       │
  │ contoso-supply-forecast    │ agentcore        │ aws   │ t.berg      │ 0oaSIMsupply0004 │ yes     │ $40       │ 51d ago       │
  │ contoso-hr-helpdesk        │ copilot_studio   │ saas  │ s.khan      │ 0oaSIMhrdesk0005 │ no      │ $10       │ 132d ago ⚠    │
  │ contoso-analytics-sql      │ snowflake_cortex │ saas  │ d.wu        │ 0oaSIManalyt0006 │ no      │ $20       │ 23d ago       │
  └────────────────────────────┴──────────────────┴───────┴─────────────┴──────────────────┴─────────┴───────────┴───────────────┘
  ▸ 6 agents · aws=2 · azure=2 · saas=2 · 2 SaaS agents governed via identity + registry (no gateway path)
  ◆ Access review overdue (> 90 days): contoso-rev-cycle-coder, contoso-hr-helpdesk — agents are reviewed like teammates

══════════════════════════════════════════════════════════════════════════════
 SCENE 03 │ Sync to ServiceNow (system of record)
          │ Table API upsert · DRY_RUN unless --authorize in azure mode
══════════════════════════════════════════════════════════════════════════════
    {
      "u_agent_id": "contoso-claims-triage",
      "u_name": "Claims Triage",
      "u_platform": "foundry",
      "u_cloud": "azure",
      "u_owner": "maria.gomez@contoso-health.example",
      "u_cost_center": "CC-1001-claims-ops",
      "u_identity_okta_app_id": "0oaSIMclaims0001",
      … (9 more lines)
  ◆ 6 DRY_RUN receipts → artifacts/mccp/receipts/demo/  (table 'x_ai_agent_registry' — VALIDATE with ServiceNow)

══════════════════════════════════════════════════════════════════════════════
 SCENE 04 │ Agents have identities: Okta tokens checked by the gateway
          │ validate-jwt (issuer, audience, expiry) + identity binding
══════════════════════════════════════════════════════════════════════════════
  ▸ Okta access token for contoso-claims-triage: iss=https://contoso-health.okta.example/oauth2/default aud=api://contoso-ai-gateway cid=0oaSIMclaims0001 ttl=15m
  ✖ impostor: coder token, header=claims-triage  HTTP 403 forbidden_or_quota · agent_identity_mismatch (choose:identity-mismatch)
  ✖ token minted for another audience            HTTP 401 unauthenticated · invalid_token (validate-jwt)

══════════════════════════════════════════════════════════════════════════════
 SCENE 05 │ Normal day: three agents, three clouds, one gateway
          │ OpenTelemetry GenAI span emitted per call
══════════════════════════════════════════════════════════════════════════════
  ✔ azure  · claims-triage    · maria.gomez      HTTP 200 allowed · 116 tokens · user quota left 4,499,884
  ✔ aws    · patient-scheduling · r.silva        HTTP 200 allowed · 104 tokens · user quota left 7,499,896
  ✔ aws    · supply-forecast  · t.berg           HTTP 200 allowed · 102 tokens · user quota left 2,499,898
    span chat gpt-4.1 gen_ai.operation.name=chat, gen_ai.request.model=gpt-4.1, gen_ai.usage.input_tokens=56, gen_ai.usage.output_tokens=60, gen_ai.agent.id=contoso-claims-triage, gen_ai.agent.name=Claims Triage

══════════════════════════════════════════════════════════════════════════════
 SCENE 06 │ Runaway: rev-cycle-coder loops on behalf of j.chen
          │ user limit $40/mo ≈ 10,500,000 tokens · already used 10,460,000 · TPM/agent 20,000
══════════════════════════════════════════════════════════════════════════════
  ✔ loop #01                                     HTTP 200 allowed · 6,908 tokens · user quota left 33,092
  ✔ loop #02                                     HTTP 200 allowed · 6,908 tokens · user quota left 26,184
  ✔ loop #03                                     HTTP 200 allowed · 6,908 tokens · user quota left 19,276
  ◆ loop #04                                     HTTP 429 throttled · tokens_per_minute_exceeded · retry in 60s
    gateway burst limit hit → agent backs off; demo clock +60s (09:00 → next minute)
  ✔ loop #05                                     HTTP 200 allowed · 6,908 tokens · user quota left 12,368
  ✔ loop #06                                     HTTP 200 allowed · 6,908 tokens · user quota left 5,460
  ◆ loop #07                                     HTTP 403 forbidden_or_quota · user_token_quota_exceeded
  ◆ Monthly per-user limit reached: the gateway now refuses j.chen's traffic until approval or month end

══════════════════════════════════════════════════════════════════════════════
 SCENE 07 │ Spend, forecast and budget status
          │ prices ILLUSTRATIVE · MTD as of 2026-11-20 · ok <80% · warn 80-100% · breach ≥100%
══════════════════════════════════════════════════════════════════════════════
  ┌────────────────────────────┬────────┬────────┬──────┬──────────┬─────────┬────────┬──────────────┐
  │ agent                      │ MTD    │ budget │ used │ forecast │ trend   │ status │ action       │
```

## Update — Nov 19 2026: Azure deployment fixes

* **Model:** NEW mode deploys `gpt-5-mini` `2025-08-07` (GA) as deployment `policy-model`, the same model the base repo's lab uses. `gpt-4.1-mini` `2025-04-14` is deprecated (retires 2027-04-14). The live client sends `max_completion_tokens` and `reasoning_effort: minimal`; `api-version` is configurable (`FOUNDRY_OPENAI_API_VERSION`, default `2025-04-01-preview`). Local demo output is byte-for-byte unchanged.
* **Existing environment:** new ATTACH mode (`--attach-rg`) reuses the lab's Foundry account, project and `policy-model` deployment from `infra/live.bicep`; the only write there is one role assignment. New modules `foundry-existing.bicep` and `foundry-access.bicep`.
* **Identity:** `identityProvider` parameter (`entra` default, `okta`). Both `validate-jwt` blocks live in `ai-gateway.xml`; `apim.bicep` comments out the unselected one. Entra lists v1 and v2 issuers so `az account get-access-token` works. `python -m mccp call --mode azure` gets an Entra token automatically.
* **No placeholder emails:** `main.parameters.json` replaced by `main.bicepparam` (reads environment variables); `deploy.sh` defaults the alert email to your `az login` user.
* **Bugs fixed from the ARM reference:** named values are not returned on GET → Logic App and `killswitch.py` now use `POST …/listValue`; subscription `scope` now `/products/agents`; App Insights logger now uses the documented `instrumentationKey` credential; ARM URL from `environment()`; policy header comment moved inside `<policies>`.
* **Resilience:** a live kill now records Okta/ServiceNow as SKIPPED when they are not configured instead of stopping after the gateway step.
* **`infra/mccp/deploy.sh`:** preflight (CLI, sign-in, providers, model/quota or lab lookup) → `az bicep build` + `build-params` → `validate` → `what-if` → deploy → `.env.mccp.azure` → HTTP 200 smoke test.
* **Tests:** 53 (was 39). New `test_infra_static.py` checks module paths, params passed vs declared, outputs referenced vs declared, `loadTextContent` paths, the bicepparam file, and both identity variants of the policy; `test_live_client.py` checks live request shapes without network calls.
* **Not done here:** `az bicep build` could not run in the build sandbox (no internet to download the Bicep CLI). `deploy.sh` runs it first and stops on any error.

## Update — Nov 19 2026 (2): self-contained `demos/` folder

* **Where it goes:** unzip into a new folder, `demos/mccp-multicloud-control-plane/`, on branch `feature/multicloud-control-plane`. Nothing is copied into the repo root and nothing is unzipped to `/tmp`. Steps are in `README.md`.
* **Stand-alone project:** `pyproject.toml` (own `.venv`; extras `azure`, `aws`, `okta`, `notebooks`; dev group `pytest`), `Makefile` (`make demo|test|whatif|deploy|clean`), `.gitignore` (`.env`, `.env.mccp.azure`, `artifacts/`, `.venv/`) and `.env.example`. Replaces `MERGE.md`, `Makefile.mccp`, `pyproject.mccp.toml` and `.env.example.mccp`, so the base repo's `pyproject.toml`, `uv.lock`, `Makefile` and `.env.example` are untouched.
* **Paths:** `.env` and `.env.mccp.azure` are loaded from the demo folder whatever the working directory. `deploy.sh` writes `.env.mccp.azure` and `artifacts/mccp/smoke-response.json` inside the demo folder (it used `/tmp` for the smoke-test response before).
* **Tests:** new `tests/mccp/test_demo_layout.py` (5 tests); 58 pass. Rehearsed the README steps in a scratch git repo: branch, `mkdir -p demos/...`, `unzip -d`, demo, tests, deploy-script syntax check; `git status` shows only `demos/mccp-multicloud-control-plane/`.
