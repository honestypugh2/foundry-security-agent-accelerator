# Workshop documentation

Start with the [participant guide](participant-lab/README.md) and
[notebook guide](../notebooks/README.md). Core labs are local and credential-free;
Azure and Agent 365 are optional, separately authorized extensions.

## Find the right reference

| Topic | Guide | Use it to |
|---|---|---|
| Architecture | [Workflow overview](architecture/overview.md) | Follow the trust boundaries and request lifecycle |
| Azure setup | [Participant Azure lab](participant-lab/azure-live-lab.md), [deployment reference](architecture/azure-deployment.md) | Distinguish existing-resource exercises from authorized provisioning |
| Security | [Threat model](security/threat-model.md), [advanced boundaries](security/advanced-threat-model.md) | Review egress, tools, delegation and evidence limitations |
| Control ownership | [Six-pillar matrix](security/six-pillar-control-matrix.md) | Separate application and native platform responsibilities |
| Evaluations | [Evidence and release gates](evaluations/framework.md) | Interpret outcomes, ASR limits and human adjudication |
| Service evaluation | [Foundry evaluation](evaluations/foundry-service.md), [red-team reconciliation](evaluations/redteam-reconciliation.md) | Keep model quality separate from security and execution |
| Observability | [Traces, correlation and completeness](observability/trace-architecture.md) | Inspect local evidence and distinguish export from ingestion |
| Agent 365 | [Integration guide](agent365/integration-architecture.md), [signal matrix](agent365/signal-scope-matrix.md) | Check identity, publication, governance, Defender and Purview independently |
| Cloud boundaries | [Commercial and Government guide](clouds/commercial-vs-government.md) | Review availability, routing and compensating controls |
| Attribution | [Reuse and attribution](reuse-and-attribution.md) | Review implementation references and licensing |

Prefer an interactive overview? Open the self-contained
[technical field guide](index.html). It is educational illustration, not service
execution. See [troubleshooting](participant-lab/troubleshooting.md),
[cleanup](participant-lab/cleanup.md) and the
[production/WAF disclaimer](participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).
