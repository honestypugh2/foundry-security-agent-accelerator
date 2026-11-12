# Reuse assessment

Strategy **A: clean repository with selective, attributed pattern adaptation**.
The workspace had no application at initialization; pre-existing editor settings
were preserved and excluded from publication. Existing source repositories were
read-only. No remote repository, branch, issue, PR or deployment was created.

GitHub authenticated successfully. Own-account inventory returned 27 accessible
repositories. The three explicitly requested repositories were prioritized.
Null GitHub license metadata was corrected by reviewing actual MIT license files.

| Candidate | Visibility/default branch | Relevant branch | License evidence | Suitability/risk |
|---|---|---|---|---|
| HR policy knowledge | Public/main | `bp/ai-governance-oct28` | Actual LICENSE: MIT | Retrieval architecture reference; do not copy HR data, images or service evidence |
| Ready enterprise platform | Public/main | main | Actual LICENSE: MIT | Strong provider/entitlement prior art; adapt only bounded pattern, not broad platform |
| Governance operating model | Private/main | main | Actual LICENSE: MIT | Reference manifests only; private visibility still requires confidentiality review beyond copyright |
| Foundry search validate | Private/main | main | Not reviewed | No code reuse authorized by this assessment |
| Foundry workload studio | Public/main | main | Not reviewed | No copied code |
| Hybrid router workshop | Public/main | main | Not reviewed | No copied code |
| Azure ML infra foundation | Public/main | main | Not reviewed | No copied infrastructure |
| Warehouse replenishment | Public/main | main | Not reviewed | No copied business-action logic |

Python versions and dependency management were confirmed only where a manifest
was actually read: the governance project uses Python 3.12 and uv, Projects 2.10,
Azure Identity and OTel. Ready platform has Python retrieval packages, evaluation
packages and Bicep modules; the HR branch distinguishes managed prompt and hosted
retrieval architectures. Their test coverage and CI outcomes were **not run or
certified** here. Other candidates remain unassessed beyond metadata.

Exact source commits, source files, modifications, tests and attribution are in
[reuse and attribution](docs/reuse-and-attribution.md).

Microsoft SDK GitHub API requests encountered organization SAML enforcement.
No access-control workaround was attempted. Official Learn generated SDK
documentation, the installed SDK signatures, and public package metadata were
used instead. This is a documented source-verification gap, not an SDK validation
or Azure service success.
