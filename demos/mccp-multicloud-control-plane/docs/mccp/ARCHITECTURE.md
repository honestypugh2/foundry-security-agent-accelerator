# mccp architecture

## Planes

| Plane | Responsibility | Product (Contoso Health demo) | Enforcement? |
|---|---|---|---|
| **Record** | Inventory, ownership, cost center, lifecycle state, incidents | ServiceNow AI Control Tower (system of record); Foundry Control Plane (Microsoft-side view) | No: it records |
| **Identity** | Who the agent is and whether it can get a token | Okta (service app per agent, private_key_jwt); Entra Agent ID for Foundry / Copilot Studio agents | Yes: no new tokens after deactivate |
| **Runtime** | Every model call: authenticate, attribute, meter, limit, stop | Azure API Management AI gateway (`ai-gateway.xml`) | Yes: works in seconds |
| **Observability** | Traces, token metrics, cost signals | OpenTelemetry GenAI → OTel Collector → Datadog + Azure Monitor | No: it alerts |
| **FinOps** | Spend per agent / user / cost center, forecast, approvals | `finops.py` + Log Analytics + Consumption budget | Through the gateway quotas |
| **Automation** | Alert → action | Azure Monitor alert / Datadog webhook → Logic App → APIM named value | Yes: kill without a human |

**Design rule:** Datadog and Azure Monitor alert, and the gateway enforces. The gateway is the one point every gateway-routed agent passes through, whatever cloud it runs in.

```mermaid
flowchart LR
  subgraph Agents
    A1[Foundry agents<br/>Azure] 
    A2[Bedrock / AgentCore<br/>AWS]
    A3[Copilot Studio<br/>SaaS]
    A4[Snowflake Cortex<br/>SaaS]
  end
  OKTA[(Okta<br/>agent identities)]
  APIM{{APIM AI gateway<br/>validate-jwt · kill lists · llm-token-limit · llm-emit-token-metric}}
  FDY[Foundry models<br/>managed identity]
  SN[(ServiceNow<br/>AI Control Tower)]
  OTEL[OTel Collector]
  DD[Datadog]
  AM[Azure Monitor<br/>App Insights + Log Analytics]
  LA[Logic App<br/>kill switch]
  A1 & A2 -- Bearer token --> APIM
  A1 & A2 -. client credentials .-> OKTA
  APIM --> FDY
  APIM -- token metrics --> AM
  A1 & A2 & A3 & A4 -- OTLP GenAI spans --> OTEL --> DD & AM
  AM -- alert --> LA
  DD -- webhook --> LA
  LA -- ARM PUT named value --> APIM
  mccp[[mccp CLI]] -- upsert / incident --> SN
  mccp -- lifecycle deactivate --> OKTA
  A3 & A4 -. identity + registry only .-> SN
```

SaaS agents (Copilot Studio, Snowflake Cortex) call their own platform's models, so their traffic does **not** pass through APIM. For these agents, the controls are identity (Okta / Entra), the registry, and platform-native admin actions. The demo marks them `gateway = no`.

## Flow 1: register

```mermaid
sequenceDiagram
  participant P as Platform adapters (Foundry, Bedrock, AgentCore)
  participant R as mccp registry
  participant SN as ServiceNow
  participant O as Okta
  P->>R: list agents (native ids)
  R->>R: merge + dedupe (agent_id, native_id), enrich owner / cost center / budget
  R->>SN: upsert CI (Table API, DRY_RUN unless --authorize)
  Note over O: one service app per agent (okta_app_id), JWKS for private_key_jwt
```

## Flow 2: runtime call

```mermaid
sequenceDiagram
  participant A as Agent
  participant O as Okta
  participant G as APIM (ai-gateway.xml)
  participant F as Foundry model
  A->>O: client_credentials + private_key_jwt
  O-->>A: access token (aud=api://contoso-ai-gateway, agent_id claim, 15 min)
  A->>G: POST /ai/openai/deployments/{d}/chat/completions<br/>Bearer + x-agent-id + x-cloud + x-cost-center
  G->>G: validate-jwt → agentId/userId → identity binding (403)
  G->>G: killswitch-global (503) → killed-agents / killed-users (423)
  G->>G: llm-token-limit agent: TPM (429) + monthly quota (403)
  G->>G: llm-token-limit user: monthly quota, tier2 if approved (403)
  G->>F: authentication-managed-identity + set-backend-service
  F-->>G: completion + usage
  G->>G: llm-emit-token-metric (agent-id, user-id, cloud, cost-center)
  G-->>A: 200 + x-remaining-tokens, x-user-remaining-quota-tokens
```

## Flow 3: budget breach → kill

```mermaid
sequenceDiagram
  participant M as Azure Monitor / Datadog
  participant L as Logic App (system MI)
  participant ARM as ARM (APIM named values)
  participant G as APIM
  participant K as mccp kill (operator)
  M->>L: alert (common alert schema: dimension agent) / webhook (alert_scope)
  L->>ARM: GET namedValues/killed-agents
  L->>ARM: PUT namedValues/killed-agents (+agent)
  G-->>G: next call from agent → 423
  K->>K: ① gateway (named value, optional subscription suspend)
  K->>K: ② identity: Okta lifecycle/deactivate, AWS IAM deny
  K->>K: ③ record: ServiceNow CI status=killed + incident
  K->>K: platform-native steps (Foundry Control Plane stop/block, Entra Agent ID disable): printed, manual
```

The order is gateway first, identity second, record third. The gateway takes effect in seconds; VALIDATE how long a named-value change takes to reach the gateway. Okta deactivation stops **new** tokens, but tokens already issued stay valid until they expire because APIM validates them locally. Keep agent token lifetimes short.

## Flow 4: revive

`mccp revive --agent X --authorize` reverses the same points: it removes X from `killed-agents`, sets the subscription to `active`, calls Okta `lifecycle/activate`, deletes the AWS deny policy, sets the ServiceNow CI to `active`, and prints the platform steps in reverse.

## Cost limits: dollars to tokens

* Each human user has a **$40/month** standard limit (`data/mccp/budgets.json`).
* `finops.PriceTable.usd_to_tokens` converts that limit to a gateway quota at the reference blended price (gpt-4.1, 70/30 input/output, ILLUSTRATIVE): $40 is about **10.5M tokens**.
* When an approver accepts a request for more, the user is added to `quota-tier2-users`, which uses a separate counter with a $80-equivalent quota.
* The token quota is model-agnostic. It is a hard backstop. `finops.py` computes the exact dollars per model and raises warn/breach and the recommended action.

## Simulator fidelity

`policy_sim.py` runs the same steps in the same order as `ai-gateway.xml`. `XML_ELEMENT_MAP` maps each step to its XML element, and `python -m mccp policy-map` and the tests check that mapping. The simulator also models the APIM subscription state check, which runs **before** any policy. That is why a `--hard` kill returns 401 rather than the clearer 423.
