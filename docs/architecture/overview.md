# Architecture: Protect / Prove / Operate

Azure governs infrastructure; Foundry governs the AI workload; Agent 365 governs
the deployed agent. Entra authenticates and authorizes identities. Defender owns
threat investigation; Purview owns data/compliance policy. Azure Monitor owns app
telemetry. These are separate enforcement and evidence surfaces.

## Per-module Azure and fallback matrix

| Module | Azure execution | Explicit local fallback |
|---|---|---|
| `config.py` | Validates tenant, subscription, cloud-specific endpoints, pinned agent, Search | Local settings; remote telemetry forbidden |
| `agent.py` | Projects 2.10.0, Entra credential, pinned no-tools prompt agent, Responses API | `LocalAgent`, deterministic synthetic response |
| `retrieval.py` | SearchClient 12.1.0, query-time entitlement equality filter, bounded results, source schema validation | `LocalRetriever`, same entitlement contract over original synthetic fixtures |
| `security.py` | Same deterministic checks plus optional ContentSafetyClient 1.0.0 input/output moderation | `LocalInspector`, injection-signature and egress/delegation controls |
| `tools.py` | Same closed read-only tool registry; actual retrieval happens through its explicit adapter | Identical policy lookup; never exposes writer |
| `policy.py` | Same authoritative deterministic amount/approval rule | Identical engine, no dependency on model availability |
| `approvals.py` | Exact approval contract and independent approver interface; production authenticated approver NOT_IMPLEMENTED | Explicit synthetic reviewer, local-only |
| `writer.py` | DRY_RUN-only SQLite receipt sink, even in Azure mode | Same idempotent sink; no real business connector |
| `audit.py` | Hash-linked local evidence; external immutable anchoring NOT_IMPLEMENTED | Same chain and independently retainable head |
| `evaluation.py` | Microsoft Foundry relevance/groundedness model judging with `azure-ai-evaluation`; project result tracking, exact row/case reconciliation; shared security gate | Explicit pytest-driven deterministic regressions; no service-equivalence claim |
| `observability.py` | Azure Monitor/Application Insights OTel exporter, read-only Log Analytics query, per-span correlation and delivery evidence | OpenTelemetry SDK JSON without network; optional standard OTLP/HTTP collector when explicitly configured outside local mode |
| `identity.py` | SDK token acquisition bound to configured tenant and tenant-scope guard; no tokens logged | No credential acquisition; synthetic identity in fixtures only |
| `workflow.py` | Routes explicit Azure providers; errors propagate; consequential proposal remains pending approval | Deterministic provider selection, synthetic approval optional |
| `agent365/` | Read-only account fields behind preview REST opt-in; structured operator observations | UNKNOWN/manual checklist, never fake registry or ingestion |
| `azure_ops.py` | Read-only account check and explicit gaps; scoped provisioning guidance | Plans/refusals only, no Azure mutation |
| `contracts.py` | Shared immutable typed service/evidence boundaries | Identical validation |
| `scenarios.py` | Shared regression expectations for normalized service evidence | Synthetic fixtures clearly labeled |
| `cli.py` | Explicit `--mode azure`; no cloud-to-local downgrade | Default `--mode local` |

“Azure and fallback” means an actual service adapter where a supported service
exists, and identical native deterministic enforcement where it does not.
There is deliberately no pretend Azure approval, policy or writer API.

## Data flow

Trusted caller -> entitlement-trimmed retrieval -> untrusted-content check ->
bounded read-only tool -> no-tools model -> output check -> deterministic policy ->
exact independent approval -> DRY_RUN receipt -> audit and trace completeness.

The Azure CLI still requires an authorized selected cloud/subscription. A valid
credential alone does not establish product licensing, region support, effective
RBAC, quota, network access or signal ingestion.
