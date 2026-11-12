# Control ownership

| Boundary | Application control | Microsoft-native complement |
|---|---|---|
| Caller identity | Explicit tenant guard and trusted entitlement contract | Entra authentication/conditional access and least-privilege RBAC |
| Retrieval | Azure Search filter plus row validation | Search data-plane RBAC/index configuration |
| Input/output | Deterministic heuristics, optional Content Safety moderation | Supported Foundry guardrails and native data protection |
| Model | Pinned no-tools prompt definition | Foundry project/model permissions and supported guardrails |
| Business action | Deterministic policy and independent exact approval | Enterprise approval identity/workflow, separately implemented |
| Evidence | Hash-linked audit, OTel spans, evaluator reconciliation | Azure Monitor and applicable product audit surfaces |
| Lifecycle | Fresh scoped operator attestations | Applicable Agent 365 owner/sponsor/inventory governance |
| Data protection | Synthetic schema, redaction | Purview native classification/audit/DLP where supported |
| Investigation | Controlled application evidence | Defender native event/alert/incident capabilities where supported |

Microsoft product names identify owners, not implemented integrations or compliance
certification. [Six-pillar matrix](six-pillar-control-matrix.md).
