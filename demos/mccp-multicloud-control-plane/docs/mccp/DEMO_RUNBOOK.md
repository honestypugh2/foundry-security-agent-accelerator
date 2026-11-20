# mccp demo runbook: Contoso Health (synthetic), about 25 minutes

**Setup (T-15 min):** open VS Code with a dark terminal at about 140 columns and a font size readable on screen share. Run the commands below once to warm up. Keep `docs/mccp/ARCHITECTURE.md` open in the Markdown preview so the mermaid diagrams render.

```bash
cd <repo>/demos/mccp-multicloud-control-plane
rm -rf artifacts/mccp
uv run python -m mccp demo --mode local --color | less -R     # rehearsal; without uv: PYTHONPATH=src python3 -m mccp ...
```

Everything shown is **SIMULATED** and runs offline. Say so at the start: "This is the local mode of the same code that runs against Azure. Every action that would change a real system shows a dry-run receipt."

| Min | Beat | Command / action | Expected output (key lines) | Talk track |
|---|---|---|---|---|
| 0–2 | Framing | ARCHITECTURE.md planes diagram | — | "Record, identity, runtime, observability. Datadog alerts; the gateway enforces." |
| 2–4 | Scene 1–2: inventory | `PYTHONPATH=src python -m mccp demo --mode local --color` (scroll as you narrate) | `6 agents · aws=2 · azure=2 · saas=2`; amber `Access review overdue … contoso-rev-cycle-coder, contoso-hr-helpdesk` | "One inventory across Foundry, Bedrock, AgentCore, Copilot Studio and Cortex. Every agent has an owner, a cost center, an Okta app and an access-review date, the same as a teammate." |
| 4–5 | Scene 3: ServiceNow | (same run) | JSON row `u_agent_id: contoso-claims-triage`; amber `6 DRY_RUN receipts` | "ServiceNow stays the system of record. We confirm the AI Control Tower table with your ServiceNow team." |
| 5–7 | Scene 4: identity | (same run) | red `HTTP 403 … agent_identity_mismatch`; red `HTTP 401 … invalid_token (validate-jwt)` | "An agent can't claim to be another agent, and a token minted for another API is rejected at the gateway." |
| 7–9 | Scene 5: normal day | (same run) | 3 green `HTTP 200 allowed` lines (azure, aws, aws) + a `gen_ai.*` span | "Three clouds, one gateway, one telemetry schema for Datadog and Azure Monitor." |
| 9–12 | Scene 6: runaway | (same run) | green loops 01–03, amber `loop #04 HTTP 429 … tokens_per_minute_exceeded`, green 05–06, amber `loop #07 HTTP 403 … user_token_quota_exceeded` | "The per-minute burst limit slows the agent down, and the monthly per-user limit ($40 ≈ 10.5M tokens) stops it." |
| 12–15 | Scene 7: spend | (same run) | red row `contoso-rev-cycle-coder … 104% … ▲ spike  breach  kill`; amber `patient-scheduling … warn`; `j.chen … 99.6% warn approve increase` | "Month-to-date spend, linear and burn-rate forecasts, and a recommended action. Prices are illustrative." |
| 15–17 | Scene 8: alert + approval | (same run) | alert JSON `recommended_action: kill`; amber approval request; green `Approved → quota-tier2-users = j.chen…`; green `HTTP 200` for j.chen | "People get an approval path; runaway agents get stopped." |
| 17–20 | Scene 9: kill switch | (same run) | `SIMULATED apim-named-value … killed-agents=contoso-rev-cycle-coder`, `DRY_RUN okta … lifecycle/deactivate`, `DRY_RUN servicenow …incident`, `MANUAL platform-native` (Foundry Control Plane / Entra Agent ID); red `HTTP 423 killed`; green claims-triage still 200 | "The gateway acts first, in seconds. Then identity, so the agent gets no new tokens. Then the record. We print the steps that need an admin instead of pretending there's an API." |
| 20–21 | Scene 10: global drill | (same run) | red `HTTP 503 global_kill`; green `Drill reverted` | "One switch stops every agent behind the gateway." |
| 21–22 | Scene 11–12: revive + summary | (same run) | green `HTTP 200` after revive; summary table 200/401/403/423/429/503 | "Every action left a receipt." Show a file from `artifacts/mccp/receipts/demo/`. |
| 22–25 | Drill-down / Q&A | `PYTHONPATH=src python -m mccp kill --agent contoso-patient-scheduling --hard` then `cat artifacts/mccp/receipts/*-kill-aws-iam-*.json` | DRY_RUN receipts incl. `iam.put_role_policy` deny and APIM subscription `PATCH … state: suspended` | "AWS agents get an IAM deny as a second backstop. Nothing happens without `--authorize`." |

## Optional live segment (only if deployed and rehearsed)
Deploy once beforehand, from `demos/mccp-multicloud-control-plane`: `infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg>` (writes `.env.mccp.azure`, ends with an HTTP 200 smoke test).
```bash
PYTHONPATH=src python3 -m mccp call   --mode azure --agent contoso-claims-triage                 # 200, uses your az login token
PYTHONPATH=src python3 -m mccp kill   --mode azure --agent contoso-claims-triage                 # DRY_RUN receipt first
PYTHONPATH=src python3 -m mccp kill   --mode azure --agent contoso-claims-triage --authorize     # real stop
PYTHONPATH=src python3 -m mccp call   --mode azure --agent contoso-claims-triage                 # expect 423 once propagated
PYTHONPATH=src python3 -m mccp revive --mode azure --agent contoso-claims-triage --authorize
```
Show the APIM named value `killed-agents` change in the portal (APIs → Named values) and the Logic App run history.

## Fallbacks
* If colours don't render: add `--no-color`. The story reads the same.
* If the terminal is too narrow: use `--format json | python -m json.tool | head -60`.
* Notebook backup: `notebooks/mccp/06_end_to_end_local.ipynb`.

## Questions to expect
* *"Does Okta deactivation stop it immediately?"* No. It stops new tokens. The gateway kill list stops traffic within seconds, which is why the gateway goes first. Keep token lifetimes short.
* *"What about Copilot Studio / Cortex?"* They don't route through APIM. They are governed through identity, the registry and platform-native admin actions. The demo marks them `gateway = no`.
* *"Is the 403 for quota real?"* The APIM docs give 429 when the tokens-per-minute limit is exceeded and 403 when the token quota is exceeded. VALIDATE this on the tier you deploy.
