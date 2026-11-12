# Agent 365 extension: read state, do not infer product evidence

Start with [prerequisites](agent365/prerequisites.md). Agent 365 inventory,
governance and activity are native platform functions. This repository does not
simulate them or publish/register agents automatically.

```bash
# Saved synthetic fixture; always prints offline / SIMULATED, never live verification:
uv run fsa azure agent-status --from-json data/agent_state/blocked_new_agent.json
uv run fsa azure agent-status --from-json data/agent_state/legacy_exception.json
# Only in your configured, authorized Azure environment; read-only:
uv run fsa azure agent-status
```

The live operation is `project.agents.get(agent_name=...)`, not a registry query.
Runtime `state`, developer `configuration_state`, `state_source` and Entra
identity/blueprint statuses are reported independently. Missing fields are
`unknown`; Entra permit status is `active`. An enabled runtime with a disabled
identity/blueprint is a legacy-exception warning, never a healthy full-enablement
claim. Changes can take up to 10 minutes to reflect.

| Intervention | Scope / effect | Repository behavior |
|---|---|---|
| Agent 365 Block / Entra disable | Identity admin state; applicable agents blocked | Interpret observed state only |
| Blueprint disable | Agents derived from that blueprint | Interpret separately from individual identity |
| Agent 365 Unblock | Removes applicable Entra restriction | Does not undo developer disable |
| Developer disable in Foundry | Workload configuration; also controls legacy agents | Explain configuration independently |
| Soft delete / restore | Native identity lifecycle | No identity mutation performed |
| Application approval deny/expire | Exact application-authored proposal | DRY_RUN writer refuses invalid approval |
| Resource cleanup | Infrastructure, not registry/activity retirement proof | Manual exact-resource review only |

Any Block exercise requires separate authorization and a disposable agent
created on/after the documented enforcement cutoff, **23 Oct 2026 16:00 UTC**.
No Block, consent, publication or disable action is executed here.

[Microsoft availability guidance](https://learn.microsoft.com/azure/foundry/control-plane/govern-agent-infrastructure-entra-admin),
[signal scope matrix](agent365/signal-scope-matrix.md),
[live lab](participant-lab/agent365-extension.md),
[requirements gaps](../REQUIREMENTS_GAP_ANALYSIS.md).
