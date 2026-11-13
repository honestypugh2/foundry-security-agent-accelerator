# Workshop documentation

Start with the [participant guide](participant-lab/README.md) and
[notebook guide](../notebooks/README.md). The recommended route is **Azure Live**:
setup -> dedicated four-tool Foundry agent -> Protect -> Prove -> Operate.
Use the [local fallback](participant-lab/local-fallback.md) when Azure is
unavailable. Agent 365/native portal observation is a separately authorized,
optional extension; it is not a prerequisite for the model/Search workshop.

## Workshop entry points

1. [Prerequisites and shared setup](../README.md#1-prerequisites-and-workshop-setup)
2. [Azure setup, roles, synthetic data and consent](participant-lab/azure-live-lab.md)
3. [Notebook order, switches and expected evidence](../notebooks/README.md)
4. [Troubleshooting](participant-lab/troubleshooting.md) and [cleanup](participant-lab/cleanup.md)

Azure-first describes the learning route, not automatic cloud execution. Defaults
remain local and all live cells require deliberate opt-in.

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
| Request -> approval -> publication | [Lab 07](participant-lab/request-approval-publish.md), [notebook](../notebooks/07_agent365_request_approval_publish.ipynb) | Demonstrate local decision boundaries and separately observe existing templates/requests without tenant changes |
| Cloud boundaries | [Commercial and Government guide](clouds/commercial-vs-government.md) | Review availability, routing and compensating controls |
| Attribution | [Reuse and attribution](reuse-and-attribution.md) | Review implementation references and licensing |

Prefer an interactive overview? Open the self-contained
[technical field guide](index.html). It is educational illustration, not service
execution. See [troubleshooting](participant-lab/troubleshooting.md),
[cleanup](participant-lab/cleanup.md) and the
[production/WAF disclaimer](participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).
