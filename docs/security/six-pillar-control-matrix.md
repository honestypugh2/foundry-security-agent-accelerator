# Six security pillars

All local statuses below concern the supplied synthetic workflow only. No live
Azure, Agent 365, Defender or Purview validation is implied.

| Pillar | Protect / Python | Prove / tests | Operate / evidence | Native owners and residual risk |
|---|---|---|---|---|
| Identity/access | `config`, `agent`, `retrieval`, `tools`; cloud endpoints, Entra credential, entitlement trimming, allowlist | `test_azure`, `test_core`: cross-cloud endpoint rejection, filter injection, unauthorized tool and row rejection | Selected-account preflight; per-run tool/security audit | Azure RBAC/Foundry project roles; Entra identity; Agent 365 owner/sponsor evidence separate. Caller entitlements need production authentication |
| Data/IP | `security`, `retrieval`; synthetic-only schema, redaction, untrusted evidence | Leakage regressions, classification rejection, no unauthorized Search row exposure | Source IDs and redacted model audit | Purview classification/DLP/audit; Defender investigation; no enterprise DLP connector implemented |
| Model security | `agent`, `security`; pinned no-tools prompt version, moderation option | Model/version/tools validation, injection fixture rejection | Model stage and output-security decisions | Foundry model/guardrails/evaluation; no universal injection or safety guarantee |
| Application/agent | `policy`, `approvals`, `writer`, `evaluation`; exact expiring independent approval, idempotency | Modification/expiry/forgery/cross-authority denial, unsafe execution despite safe answer | DRY_RUN receipt, reconciled raw evidence | App deterministic enforcement; Agent 365 lifecycle governance is separate; production human approval service absent |
| Infrastructure/network | `config`, `security`, Bicep; HTTPS/cloud suffixes, egress allowlist | Cloud endpoint/egress tests; Bicep compilation | Azure what-if, cloud diagnostics when authorized | Azure Policy/network; Defender CSPM; public lab template is not private isolated; government support unresolved |
| Operations | `audit`, `observability`, `agent365`; hash chain, W3C correlation, optional Monitor | Tamper/truncation, trace gaps, missing Agent 365 evidence | OTel JSON, manual registry/activity observations | Azure Monitor telemetry; Foundry workload traces; Agent 365 inventory/lifecycle; Defender incidents; Purview audit. External anchoring/ingestion not validated |

Licensing and per-cloud limitations are explicit gates, not silently compensated
by successful local tests. No failed Foundry evaluation is assumed to generate
a Defender alert, and no Registry entry is assumed to prove Purview coverage.
