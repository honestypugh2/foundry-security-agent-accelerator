# Optional Agent 365 extension

Core Foundry execution does not require Agent 365 licensing.
Preferred guide: [05 extension notebook](../../notebooks/05_agent365_extension.ipynb).
Expected duration 20 minutes plus any platform sync; L300-L400. Complete
[setup](../../notebooks/00_environment_setup.ipynb) first. Bash and PowerShell:
`uv sync --frozen --all-extras --dev`. The executable/module entry points
are equivalent: `uv run python -m fsa agent365 preflight`.
Use an explicitly configured private `FSA_MODE=azure` for authorized nested
Agent 365 status reads; the top-level global mode is not forwarded to this
subparser. No notebook or command automatically changes consent/governance.
See [integration status](../AGENT365_INTEGRATION_STATUS.md) for evidence labels,
[troubleshooting](troubleshooting.md), and [cleanup](cleanup.md).

Read [the integration source](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-365-integration)
and [collection prerequisites](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection).
Confirm current SKU, tenant consent and administrator role requirements with
your tenant administrator; do not change licensing or consent from the lab.

```bash
uv run fsa agent365 preflight
uv run fsa agent365 status
# Optional read-only use of the specifically documented preview ARM API:
uv run fsa agent365 status --preview-api
uv run fsa agent365 verify --evidence path/to/private-observations.json
```

Missing checks return nonzero and VERIFICATION_REQUIRED, not success.
Default local mode performs no Azure request. Azure account status requires the
configured resource group/account and selected Azure cloud. Field inspection uses
documented `2026-03-15-preview` only with explicit opt-in.

## Optional read-only portal observation

In your own authorized environment, the workshop can include Agent 365 and
Defender portal observation without provisioning or administrative changes.
Keep tenant identifiers, identities, resource addresses and screenshots private.

- In Agent 365, inspect the actual inventory entry and its visible governance
  state. Record owner/sponsor, identity and activity only when actually visible;
  an inventory entry alone does not establish activity ingestion.
- In Defender, identify the visible resource or agent scope and observation
  time. Show existing findings only; do not generate attacks or promise an alert.
  A deployment finding is not automatically an agent-specific detection.
- Distinguish the portal evidence from local synthetic scenarios and DRY_RUN
  receipts. A portal observation does not validate the repository's adapters,
  Foundry IQ retrieval, or Monitor ingestion.
- If an expected item is absent or access is unavailable, retain that gap and
  continue with the labeled local exercises. Do not change consent, identity,
  Block/Unblock, policies or publication state during this observation.

## Separate observations

1. Confirm license and tenant consent independently.
2. Confirm prompt-agent publishing path and applicable identity.
3. In the supported Microsoft 365 administrative agent inventory, locate the
   actual agent and record its stable identifier and time.
4. Confirm Entra agent identity, owner and sponsor; do not substitute the app's
   DefaultAzureCredential caller for an agent identity.
5. Confirm an actual correlated activity event, not only a registry entry.
6. Review Defender and Purview independently; absence of a signal is not proof
   that no action occurred.

`Observation` JSON is an array with `capability`, `tenant`, `agent`, `observer`,
`observed_at` (UTC), `evidence_url`, `status`, `notes`. Required capabilities:
`license`, `consent`, `registry`, `identity`, `owner`, `sponsor`, `activity`.
Evidence must match the configured tenant/agent, be no older than 24 hours, and
have no duplicate capability. A resulting PASS means complete **operator
attestation**, never automated service validation. Keep observation files private
under ignored `artifacts/`; they can contain tenant and identity metadata.

Blocking/unblocking, disablement, retirement, MCP approval and consent changes
are NOT performed by the adapter. Use a documented synthetic walkthrough by
default; actual administrative action requires explicit independent authorization.
Hosted agents have separate SDK/telemetry requirements; this lab selects a
prompt agent. Government/GCC/GCC High/DoD availability is VERIFICATION_REQUIRED.
