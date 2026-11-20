# mccp — Multi-cloud AI Control Plane (add-on)

One inventory, agent identities, monthly dollar limits with approval, and a kill switch that actually stops agents.
The add-on works with agents in **Azure (Microsoft Foundry)**, **AWS (Bedrock / AgentCore)** and **SaaS (Copilot Studio, Snowflake Cortex, ServiceNow)**.

| Concern | Component | mccp module |
|---|---|---|
| Single source of truth | ServiceNow AI Control Tower (registry), Foundry Control Plane | `registry.py`, `servicenow.py` |
| Agent identity | Okta (one service app per agent), Entra Agent ID for Microsoft agents | `okta.py` |
| Runtime enforcement | Azure API Management AI gateway | `infra/mccp/policies/ai-gateway.xml`, `policy_sim.py`, `gateway.py` |
| Observability | OpenTelemetry GenAI → Azure Monitor + Datadog | `telemetry.py`, `otel/`, `datadog/` |
| Cost limits | Per-agent / per-user / per-cost-center budgets | `finops.py` |
| Kill switch | APIM named values + subscription, Okta, ServiceNow, AWS IAM, platform steps | `killswitch.py` |

All data is synthetic ("Contoso Health", prefix `contoso`). Local mode is offline, deterministic and labelled **SIMULATED**.

## Quick start

```bash
# offline demo: stdlib only
cd <repo>/demos/mccp-multicloud-control-plane
uv run python -m mccp demo --mode local                  # without uv: PYTHONPATH=src python3 -m mccp demo --mode local
uv run python -m mccp demo --format json                 # same story as JSON
uv run pytest -q                                         # or: python3 -m unittest discover -s tests/mccp
```

## Commands

| Command | What it shows |
|---|---|
| `demo` | The 12-scene story: inventory → ServiceNow sync → identity → allowed calls → runaway (429, then 403) → spend & forecast → alert + approval → kill (423) → global drill (503) → revive (200) → summary |
| `inventory [--format json]` | The unified inventory (fixture in local mode; Foundry/Bedrock/AgentCore adapters + fixture in azure mode, with warnings instead of made-up rows) |
| `sync-servicenow [--authorize]` | Table API upsert payloads; DRY_RUN receipts unless authorized in azure mode |
| `call --agent A --user U [--prompt P]` | One call through the gateway (simulator locally; APIM with an Okta token in azure mode) |
| `spend --scope agent\|user\|cost_center` | MTD spend, linear + burn-rate forecast, status, recommended action |
| `alert-payload --agent A` | The Azure Monitor common-alert-schema payload the kill-switch Logic App receives |
| `kill --agent A \| --user U \| --global [--hard] [--authorize]` | Kill switch across every enforcement point (receipts in `artifacts/mccp/receipts/`) |
| `revive ...` | Reverses the kill |
| `approve --user U --approver X [--authorize]` | Approval for more: adds the user to the `quota-tier2-users` named value |
| `policy-map` | Checks that every APIM XML element has a simulator function |

Common flags: `--mode local|azure`, `--format text|json`, `--no-color`, `--color`.
Without `--authorize`, every mutation writes a **DRY_RUN** receipt and changes nothing.
In local mode, `--authorize` changes only the simulated gateway (`artifacts/mccp/local_state.json`); Okta, ServiceNow and AWS stay DRY_RUN.

## Docs

* [docs/mccp/PLAN.md](../docs/mccp/PLAN.md): prerequisites, VS Code setup, Azure portal steps, run order, rollback, cost
* [docs/mccp/ARCHITECTURE.md](../docs/mccp/ARCHITECTURE.md): planes, flows, diagrams
* [docs/mccp/DEMO_RUNBOOK.md](../docs/mccp/DEMO_RUNBOOK.md): minute-by-minute demo script
* [infra/mccp/README.md](../infra/mccp/README.md): deploy, what-if, cleanup
* [README.md](../README.md): set up in `demos/mccp-multicloud-control-plane`, branch, unzip, run, commit

## Honesty notes

* Prices in `data/mccp/prices.json` are **ILLUSTRATIVE**.
* Items marked **VALIDATE** in code and docs are product facts to confirm before a live deployment: the ServiceNow AI Control Tower table/API, Foundry Control Plane stop/block blade names, Entra Agent ID availability, APIM quota status codes and counting windows, named-value propagation time, and Datadog metric naming for OTel histograms.
* Some steps have no programmatic API that mccp uses (Foundry Control Plane stop/block, Entra Agent ID disable, Copilot Studio quarantine). For these, mccp prints the admin steps and does not call an API.
