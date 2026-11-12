# Commercial and government boundaries

| Boundary | Commercial | Azure Government | Microsoft 365 GCC / GCC High / DoD |
|---|---|---|---|
| Entra authority | `login.microsoftonline.com` | `login.microsoftonline.us` | Confirm per M365 environment independently |
| ARM | `management.azure.com` | `management.usgovcloudapi.net` | Not an M365 API endpoint |
| Search audience | `https://search.azure.com` | `https://search.azure.us` | Does not establish M365 availability |
| Cognitive audience | `https://cognitiveservices.azure.com/.default` | `https://cognitiveservices.azure.us/.default` | Separate product verification |
| Foundry prompt/Agent 365 features | Require region, quota, licensing and consent verification | VERIFICATION_REQUIRED per service/region/API | VERIFICATION_REQUIRED independently |

Endpoint suffix configuration is not a feature-availability assertion. The
application rejects cross-cloud endpoint mismatches. It never transfers data
between clouds automatically.

Consult [Azure Government guidance](https://learn.microsoft.com/azure/azure-government/)
and each individual product's current availability documentation. Do not infer
Agent 365, Defender AI, Purview or sovereign-cloud support from another product's
availability. Compensating controls: native RBAC, deterministic tool policies,
local auditable receipts, separate in-cloud telemetry, manual inventory, and
approved aggregate reporting without raw cross-cloud data movement.

## Verify feature availability separately

| Capability | Commercial | Government |
|---|---|---|
| Local synthetic workflow and HTML | Local, cloud-independent | Local, cloud-independent |
| Foundry prompt agent | Verify service, region, quota and authorization | Routing support does not establish service/API availability |
| Search / Content Safety | Verify index/schema, regional service and RBAC | Suffix validation does not establish feature or region availability |
| Foundry model-judged evaluation | Implemented with explicit authorization | Rejected until a supported route is verified |
| Monitor / Log Analytics | Export/query requires independent ingestion evidence | Verify service, destination and availability separately |
| Agent 365 / Defender / Purview | Capability-specific license, consent and observation | No commercial parity assumption |

Consult current official service documentation before a live exercise. Package
installation, endpoint syntax and Bicep compilation establish none of these facts.

## Report centrally; enforce natively

Select one explicit cloud per execution. Azure resources, Foundry workload,
Entra identity and applicable Agent 365 governance remain separate authorities.
Defender and Purview retain their own signal/policy scopes. No cross-cloud
administrator credential or model-dispatched control plane is provided.

Portable policy, approval, DRY_RUN receipt, audit and telemetry contracts are
shared; credentials, audiences, endpoints and availability are verified per cloud.
Azure errors terminate the Azure run. An explicitly chosen local lab neither
replays cloud data nor establishes equivalent native governance coverage.

Do not route Government content to commercial evaluators or collectors to make
the lab pass. Cross-cloud data transfer is not implemented or authorized.
Central reporting may use only independently approved metadata/evidence.

## Record compensating controls without hiding gaps

For an unavailable control, record affected data/threat, proposed compensation,
owner, evidence and expiration. An authorized risk owner, never a model, decides
acceptance. Examples include network-free synthetic exercises, approved private
local telemetry storage, or manual review while an integration is not observable.

These are not equivalent to native Agent 365 governance, Defender prevention,
Purview DLP or service-backed evaluation. Missing critical enforcement blocks
release. Automatic commercial routing, synthetic live proof and credential
escalation are not compensating controls. See [release gates](../evaluations/framework.md#apply-a-fail-closed-gate).
