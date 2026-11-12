# Tenant-neutral Azure setup

Use the [existing-project participant lab](participant-lab/azure-live-lab.md)
for Bash and PowerShell. Python 3.12 and frozen dependencies are required; the
reference spec's zero-install path is not implemented in this repository.

## Observed presenter-lab status

The authorized isolated commercial lab deployed **new Microsoft Foundry**, not
classic: an AI Services account with project management enabled and a
`Microsoft.CognitiveServices/accounts/projects` project. A GA `gpt-5-mini`
deployment, Search, Content Safety, Log Analytics and Application Insights were
provisioned. Five operator lab grants were verified at resource scope.

Real synthetic Search/moderation/pinned-agent workflow runs returned
`AWAITING_APPROVAL`, with verified audit heads and no writer call. A separate
Log Analytics query observed seven application spans. This is not a shared
participant endpoint or Agent 365/Defender/Purview validation. Private deployment
values stay in the operator's ignored configuration.

Foundry/model/Safety/monitoring used eastus2; Search used eastus after an explicitly
approved capacity recovery. This is an observation, not a region guarantee.
Search Basic was quoted at USD0.101/hour (~USD2.42/day); other usage is additional.
No automatic deletion or hard spending cap exists.

## Configure your own environment

1. Confirm your authorized cloud/subscription/project, region, model quota,
   supported API, least-privilege roles and network access. No shared presenter
   tenant or endpoint is required.
2. Copy the example environment file into ignored `.env`; supply your private
   tenant, subscription, project, model, Search endpoint/index and pinned agent
   version. Status currently uses the same validated Settings contract as the
   workflow, including Search/model prerequisites.
3. Authenticate yourself using supported Entra tooling; the application does not
   log in, grant roles, change consent or create identities automatically.
4. Run preflight and preserve unresolved checks. To inspect an existing workload:

```bash
uv run fsa azure preflight
uv run fsa azure agent-status
```

The second command is a real read-only SDK get, not model invocation. A successful
read is not Agent 365 registration/activity or Defender/Purview evidence.
A real read succeeded in the isolated lab; your project's missing states still
remain unknown and must not be inferred from that observation.

5. Obtain separate approval before agent creation, invocation cost, judge
   evaluation/data upload or telemetry export. Follow the
   [Foundry evaluation guide](evaluations/foundry-service.md) and
   [observability guide](observability/trace-architecture.md).
6. Verify each product integration separately. Government availability remains
   [capability-specific](clouds/feature-availability.md).

The installed evaluation SDK's chat judge can internally retry up to ten times.
An authorization for four judge calls is recorded, but no judge run has been
submitted until a supported bounded configuration is verified. Do not equate
the local 16-case gate with a real Foundry service quality evaluation.

For a no-cloud rehearsal, use `agent-status --from-json` and the explicitly
synthetic reconciliation fixture. Those outputs must remain labeled offline.
See the [participant Azure lab](participant-lab/azure-live-lab.md);
no deployment or cleanup is automatic.
