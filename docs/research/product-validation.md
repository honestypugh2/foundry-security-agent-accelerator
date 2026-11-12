# Product and SDK validation ledger

Validation date: **2026-11-11**. This is documentation/package/signature validation,
not observed live service validation.

| Product/claim | Verified source | Version/status | Limitations |
|---|---|---|---|
| Foundry project/prompt agent SDK | [prompt quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/prompt-agent), [Python SDK](https://learn.microsoft.com/python/api/overview/azure/ai-projects-readme) | `azure-ai-projects==2.10.0`, current stable package from PyPI; installed `create_version/get_version/get_openai_client` signatures checked | Azure invocation, registry synchronization and government availability not observed |
| Azure AI Search SDK | [SDK README](https://learn.microsoft.com/python/api/overview/azure/search-documents-readme), [keyless code](https://learn.microsoft.com/azure/search/search-security-rbac-client-code) | `azure-search-documents==12.1.0`, stable latest reported by PyPI | Uses stable index search, not a fictional Foundry IQ API. No Search service provisioned or queried |
| Azure AI Content Safety SDK | [SDK README](https://learn.microsoft.com/python/api/overview/azure/ai-contentsafety-readme), [quickstart](https://learn.microsoft.com/azure/ai-services/content-safety/quickstart-text) | `azure-ai-contentsafety==1.0.0`, stable latest reported by PyPI | Category moderation is not Prompt Shields, DLP, or proof of injection resistance |
| Foundry evaluation SDK | [SDK README](https://learn.microsoft.com/python/api/overview/azure/ai-evaluation-readme), [RelevanceEvaluator](https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation.relevanceevaluator), [GroundednessEvaluator](https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator) | `azure-ai-evaluation==1.18.11` stable package; real batch adapter with project tracking and 1–5 quality scoring | Mocked SDK boundaries validated locally; no service evaluation performed. Quality is not security release. Experimental ContentSafetyEvaluator not enabled |
| Agent 365 data-collection fields | [configuration](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection) | Source ms.date 2026-09-29, updated 2026-09-30; documented REST `2026-03-15-preview` | Explicit `--preview-api`; account scope; active license + tenant consent + enabled flag required. Setting != ingestion |
| Agent 365 integration | [Foundry integration](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-365-integration), [connect existing agents](https://learn.microsoft.com/microsoft-agent-365/connect-existing-agents) | Selected agent: ordinary prompt agent | Registry/owner/sponsor/activity checked separately via operator evidence; no stable registry API invented |
| Agent identity | [identity concepts](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity) | Entra / agent-type-dependent | DefaultAzureCredential caller identity is not proof of an agent identity, sponsor or owner |
| Foundry agent availability | [admin availability](https://learn.microsoft.com/azure/foundry/control-plane/govern-agent-infrastructure-entra-admin) | Read-only installed `AgentsOperations.get` signature and `AgentDetails` model checked; documentation fetched 2026-11-12 | Entra status is `active`/`disabled`; runtime state is `enabled`/`disabled`; legacy cutoff and 10-minute propagation documented. Saved fixtures are offline; no live read performed |
| Azure Monitor | [Python distribution](https://learn.microsoft.com/python/api/overview/azure/monitor-opentelemetry-readme), [Logs Query](https://learn.microsoft.com/python/api/overview/azure/monitor-query-readme) | Optional stable distribution 1.8.12; `azure-monitor-query==2.0.0`; batch span export and read-only scoped KQL implemented | Stable distro includes beta exporter/instrumentation dependencies. Optional extra; not all-transitives GA. Export success != observed ingestion |
| OpenTelemetry alternatives | [Python](https://opentelemetry.io/docs/languages/python/) | Upstream SDK JSON; stable OTLP/HTTP package 1.45.2 | No backend started or ingestion assumed. Local mode forbids all remote exporters |

Official SDK implementation repository:
[Azure/azure-sdk-for-python](https://github.com/Azure/azure-sdk-for-python).
Authenticated GitHub API access to that organization returned SAML enforcement;
that check is BLOCKED_BY_PERMISSION. No bypass was attempted. Learn-generated
reference links point to MicrosoftDocs SDK source commits.

For source update dates not explicitly captured above, update date is UNKNOWN,
not guessed. Product GA, preview and availability must be scoped per capability,
agent type, cloud and license; stable package version alone cannot establish them.

## Version discipline

`uv.lock` records exact versions. Azure package versions above were checked
against public PyPI release metadata. Prefer the latest compatible stable
release, inspect Learn and SDK signatures, regenerate lock intentionally,
run `uv sync --frozen --all-extras --dev`, then `make validate`.
Never copy a future SDK method from a blog without checking the installed API.
