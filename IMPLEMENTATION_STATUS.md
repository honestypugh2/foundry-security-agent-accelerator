# Implementation status

## Session-day alignment addendum

The existing runtime is preserved. Added thin `python -m fsa` compatibility;
offline/config-only doctor, redacted CLI-account whoami, path-required audit
alias and governed synthetic-role ask. No alternate agent implementation.
Explicit local settings exclude private dotenv and remote exporters.
Seven optional notebooks use the existing package; five local notebooks execute
under service-network-denied validation, while both Azure notebooks are excluded
from PR execution. Existing CI now runs that validator.
Final local validation: 141 tests passed; measured coverage 98.49%;
`make validate` passed, including notebook execution and Bicep compilation.

Cowork output was found and inventoried; its four labs describe another runtime.
Objectives were adapted, not source prose/code/outputs imported. Extra lifecycle,
approval-queue and retention-corpus behavior remain absent. Existing live claims
below are historical, **not revalidated during this alignment**.
See [historical alignment results](docs/APEX_VALIDATION_RESULTS.md) and the
[production/WAF disclaimer](docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).

Updated: 2026-11-12 UTC. Scope: locally validated accelerator plus an authorized
isolated commercial Azure lab; not a production-certified application.

## Implemented and locally verified

- Python 3.12 frozen project; typed contracts; shared deterministic security,
  policy, independent exact expiring approval and DRY_RUN-only writer.
- Real stable Azure SDK adapters for pinned no-tools Foundry prompt agents,
  Azure AI Search and Azure AI Content Safety.
- Microsoft Foundry relevance/groundedness evaluation, explicit remote
  authorization, raw evidence preservation and unique case/result reconciliation.
- Azure Monitor/Application Insights OTel export with explicit failure reporting;
  read-only bounded Log Analytics correlation query.
- Explicit open-source fallback paths: deterministic local providers/pytest
  regressions, upstream OTel JSON and optional standard OTLP/HTTP collector export.
- Scoped read-only Agent 365 settings inspection with explicit preview opt-in;
  fresh operator-attestation verification, without fabricated remote API success.
- Read-only Foundry agent availability inspection and explicitly offline saved
  state interpretation, including developer/Entra disablement and legacy warnings.
- Seven-layer red-team reconciliation with raw byte snapshot, selected-sample
  rates, pending adjudication, UNKNOWN/unsafe strict rejection and evidence inventory.
- Input screening before retrieval, application-enforced approved-source citations,
  first broken audit-line diagnostics and dedicated unsafe-must-fail CI check.
- Actual same-workflow 16-case threshold gate, six persisted rehearsal scenes,
  validated audit/trace trees and unique-prefix/S1–S6 aliases.
- Physical 23-slide, 45-minute presentation; 12 explorers, 54 controls,
  desktop/mobile offline Chromium checks.
- New Foundry account/project, GA model, Search, Content Safety, Logs/Insights
  deployed through reviewed Bicep; all five lab operator grants at resource scope.
- Requested documentation paths, including labs, security/control ownership,
  presenter script, signal boundaries and technical/evidence reports.

Native enforcement modules are deliberately shared across modes. There is no
invented cloud policy/approval/write API simply to label every module "Azure".
Cloud errors terminate; switching to local starts a separately labeled run.

## Verified live in the approved synthetic lab

- **New Foundry only**: AI Services account with project management enabled and
  a `Microsoft.CognitiveServices/accounts/projects` project; no classic hub.
- GA `gpt-5-mini` version `2025-08-07`; real prompt-agent creation/read and pinned,
  no-tools invocation through the current `agent_reference` body.
- Azure AI Search synthetic entitlement filtering and Content Safety moderation.
- Real shared workflow returns `AWAITING_APPROVAL`; audit head verifies;
  no writer call or business mutation.
- Monitor delivery and seven correlated application spans read from Log Analytics.
  Delivery alone is not ingestion proof; the retained query is separate evidence.

## Not implemented or not live-validated

- No production authenticated caller/entitlement or human-approval service.
- No live business writer, remote MCP server or autonomous multi-agent system.
- No automatic provisioning wrapper: authorized operators use reviewed Bicep
  what-if/deployment guidance; the scoped lab was deployed manually.
- Foundry service quality judge not executed: four calls authorized, but the
  current chat-evaluator path can retry beyond that limit. Requires a supported
  bounded configuration; no extra model/permissions provisioned to bypass it.
- No Agent 365 publication/consent/identity changes or registry/activity,
  Defender alert or Purview DLP/audit integration observed.
- Government feature parity, cloud quota/RBAC/policy acceptance and private
  networking remain environment-specific verification work.
- Chapter-specific private source content was not accessed or license-verified;
  official public-source implementation is mapped separately.

See [validation evidence](VALIDATION_EVIDENCE.md) and
[technical validation](L600_TECHNICAL_VALIDATION.md). Local readiness is not
permission to deploy, publish, mutate tenant settings or claim service success.

## v0.2 specification comparison

The [requirements gap analysis](REQUIREMENTS_GAP_ANALYSIS.md) maps all specification
sections and acceptance criteria. This is not the reference v0.2 runtime:
package/Python baseline and validated enforcement are retained. Bare-stdlib
execution, persona/clearance planning, persistent approval queue, reference
unsafe-runtime benchmark remain explicit gaps. Safe module/doctor/whoami/ask/audit
compatibility is now provided; other reference commands are not implied.
The presentation-to-code matrix is retained locally as presenter-only material;
reference appendices remain unimplemented.
