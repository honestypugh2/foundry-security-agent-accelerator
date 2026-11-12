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
