# Threat model

Assets: policy content, caller entitlements, approval authority, receipt integrity,
credentials, trace/audit evidence and release decisions.

Trust boundaries: caller -> authenticated application; untrusted retrieval ->
model context; model -> application decision; proposal -> independent approver;
approved proposal -> DRY_RUN writer; process -> optional telemetry/evaluation cloud.

| Threat | Implemented control | Residual risk |
|---|---|---|
| Indirect prompt injection | Evidence marked untrusted; deterministic signatures; pinned no-tools model | Heuristics are incomplete; model output is not an enforcement boundary |
| Unauthorized retrieval | Server-side entitlement filter, escaped OData, secondary row validation | Production entitlement authentication is not implemented |
| Tool abuse | Closed typed read-only registry; model cannot dispatch writer | New tools require explicit review |
| Write/approval forgery | Exact proposal fingerprint, independent authority, expiration, scope checks | Production human approval identity is absent |
| Leakage | Redacted audit, controlled exception categories, synthetic-only dataset | A full DLP system and arbitrary-secret detector are not implemented |
| False clean evaluation | Raw evidence, execution precedence, missing-evidence gates | Model judges remain fallible; fixtures are not ASR evidence |
| Audit mutation | Linked hashes and retained expected head | Complete rewrite requires external anchoring to detect |

No live business writer or destructive security exercise is supplied.
[Advanced cases](advanced-threat-model.md), [controls](control-mapping.md).
