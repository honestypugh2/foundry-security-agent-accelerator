# Source-to-code mapping

| Official source | Implementation boundary | Local validation |
|---|---|---|
| [Foundry prompt quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/prompt-agent) | `agent.py`: stable SDK version creation, pinned no-tools invocation | Mocked installed SDK models and client calls |
| [Search keyless SDK](https://learn.microsoft.com/azure/search/search-security-rbac-client-code) | `retrieval.py`: SDK SearchClient, cloud audience, entitlement filter | Query contract, escaping and unauthorized row tests |
| [Content Safety](https://learn.microsoft.com/azure/ai-services/content-safety/quickstart-text) | `security.py`: explicit category moderation | Installed response model and missing-category tests |
| [Evaluation SDK](https://learn.microsoft.com/python/api/overview/azure/ai-evaluation-readme) | `evaluation.py`: judge batch, project tracking, raw/result separation | Mocked evaluators, malformed/duplicate/missing evidence |
| [Azure Monitor Python](https://learn.microsoft.com/python/api/overview/azure/monitor-opentelemetry-readme) | `observability.py`: OTel batch export | Delivery failure and explicit routing tests |
| [Log Analytics SDK](https://learn.microsoft.com/python/api/overview/azure/monitor-query-readme) | `observability.py`: bounded read-only correlation query | Empty/partial/scoped result tests |
| [Agent 365 data collection](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection) | `agent365`: explicit preview account inspection | Mocked ARM output, license/enablement semantics |

Official documentation and installed API compatibility are not observed service
success. Repository-source permission gaps are recorded in the
[product ledger](product-validation.md). Reused MIT patterns are credited in
[attribution](../reuse-and-attribution.md); private content is not reproduced.

## Repository-pattern reuse trace

| Source | Concept | Module | Test | Demonstration | Documentation | Status/evidence |
|---|---|---|---|---|---|---|
| MIT `ready-enterprise-ai-platform`, exact reviewed commit in attribution | Server-side entitlement trimming and explicit provider selection | `retrieval.py` | `test_azure.py`: filter escaping, empty entitlements, rejected unauthorized rows | Local/Azure retrieval stage, explicitly selected | Architecture matrix and live lab | Adapted with notice; deterministic tests pass; Azure service query unperformed |
| Requested HR-policy repository/branch | Architecture reference only | No source/data copied | No copied-code validation claim | Synthetic policy scenario only | Reuse assessment | LICENSE/tree/docs inspected; not a claim that the source application runs here |
| Requested governance operating-model repository | Governance/dependency reference only | No source/data copied | Native project tests only | Ownership and evidence boundaries | Governance/runbook pages | Manifest/tree/license inspected; no private content reproduced |
