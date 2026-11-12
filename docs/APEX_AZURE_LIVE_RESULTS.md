# Azure live demo evidence - 12 November 2026

## Decision

**GO for the bounded synthetic Azure Search + Foundry equipment-policy demo.**
**PARTIAL for full integration validation.** Monitor ingestion is unverified;
Foundry IQ retrieval is unavailable because knowledge-base discovery returned
no configured knowledge base on the selected Search service.

These are real service observations, not conclusions from source-file presence.
The successful core run started at **17:25:44 UTC** and finished at **17:26:33 UTC**.
The signed-in account selection matched private configuration. No identifiers,
endpoints, credentials, response text or customer data appear in this report.

## Observed results

| Check | Result | Boundary |
|---|---|---|
| Configuration and CLI account selection | PASS | Not proof of effective SDK identity or role inventory |
| Azure AI Search | PASS | Live query returned nonempty employee-entitled synthetic evidence; application validates schema and entitlements |
| Empty entitlements | PASS | Denied locally before Search; not a service-side guest authorization test |
| Content Safety | PASS | Actual category moderation, not Prompt Shields or DLP |
| Foundry agent read | PASS | Existing agent was read; not Agent 365 registry verification |
| Pinned prompt-agent invocation | PASS | Actual nonempty response; version, expected model and no remote tools checked |
| Governed workflow | PASS | Actual Search/moderation/model path stopped at AWAITING_APPROVAL |
| Audit and local application traces | PASS | Audit head verified; required execution stages present |
| Writer | NOT_EXECUTED | No receipt database; no approval supplied |
| Guest/tool denial | PASS | Azure-mode application rejected a synthetic guest before the model |
| Injection denial | PASS | Deterministic local signature rejected input before retrieval/model; not a remote injection-protection claim |
| Azure Monitor ingestion | NOT_CONFIGURED | Export disabled and connection configuration absent; workspace configuration alone is not ingestion |
| Foundry IQ | NOT_CONFIGURED | Actual read-only knowledge-base enumeration returned none; no IQ retrieval call made |

Exactly **two model calls** were made by the successful core run. The first
attempt stopped at configuration before any model call. IQ discovery made no
model call. The authorized four-call budget therefore has two calls remaining;
do not treat that as permission to provision resources or run an unbounded judge.

Private per-run audits/spans and sanitized summaries are under ignored
`.fsa/live-validation/`. Summaries are retained separately from model answers.
The validator exits **1** for FAIL or PARTIAL, even when individual core checks
passed. It never falls back to local mode.

## Today's presenter commands

The following command repeats the real checks and can incur **two more model
calls**, Search/moderation costs, and configured telemetry. Run only within the
remaining authorization:

```text
uv run python -m foundry_security_accelerator.live_validation --authorize
```

In the currently configured environment expect the core checks to pass
conditionally on current service health, followed by PARTIAL / exit 1 for
unconfigured Monitor export. Today's successful observation is not a guarantee
that a later invocation will pass.

Read-only IQ discovery, no inference or resource creation:

```text
uv run python -m foundry_security_accelerator.live_validation --authorize --discover-iq
```

Expected current disposition: NOT_CONFIGURED / exit 1. Do not present ordinary
index Search as Foundry IQ agentic retrieval.

Use [notebook 01](../notebooks/01_foundry_agent_live.ipynb) for the complete
bounded validator and separate IQ discovery.
[Notebook 02](../notebooks/02_protect_identity_and_tools.ipynb) now includes an
OFF-by-default, explicitly authorized live Search/moderation section with no
model invocation. Its ordinary local path remains network-free.

## Demo story data - staged, not uploaded

[Four original synthetic documents](../data/synthetic/demo-search-documents.json)
are staged locally for the equipment-request story:

- A 400-credit monitor request must await independent approval.
- Approval is exact, independent and expiring; changing the proposal invalidates it.
- A request above 1500 credits is denied.
- Finance evidence is restricted to the synthetic finance entitlement.

The documents match the application's evidence fields and use
`classification=synthetic`. They are **not uploaded**, not automatically used
by the local fixture, and not proof that the existing live index contains all
four records. The successful live test used the pre-existing synthetic index.
The workflow's model prompt is fixed to equipment policy; it is not a generic
question-answering application.

### Remaining setup before an IQ demo

1. Review the real target index key/schema and authorize the exact four-document
   upload or merge. Preserve existing records; do not overwrite an unknown index.
2. Independently verify semantic capability, index semantic configuration,
   regional availability and cost. The repository teaching template disables
   semantic Search by default; this does not establish deployed settings.
3. Review and separately authorize creating a Search-index knowledge source and
   knowledge base scoped only to approved synthetic data. Review model usage,
   source permissions, query filtering and any service-identity grants first.
4. Perform actual bounded knowledge-base retrieval and inspect references.
   Listing a knowledge base, SDK support or a staged JSON file is not retrieval.

No source/index creation, upload, semantic setting, identity, permission, consent
or deployment changes were made. See Microsoft's
[retrieval documentation](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve?pivots=python).

## Limits and safety

No Agent 365 registry/activity, Defender/Purview connector, real-user Entra/OBO,
Foundry service judge, production writer, or GitHub-hosted CI validation occurred.
No remote push, publication or visibility change occurred during that live test.
Production readiness remains a separate review; see the
[production/WAF disclaimer](participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).

Implementation: [live validator](../src/foundry_security_accelerator/live_validation.py).
Deterministic regression checks use synthetic service doubles, not live service
evidence. The standard local suite remains separate from authorized live tests.

## Local regression validation after these changes

`UV_OFFLINE=1 AZURE_BICEP_CHECK_VERSION=false make validate` passed:
**149 tests**, **96.54%** measured coverage, **66** selected security/evaluation
tests, Ruff lint/format and strict Pyright. All seven notebooks passed source
validation; five default local paths executed under network/credential denial.
Azure notebook execution is excluded from that local validation.
The four staged documents passed the runtime evidence schema and unique-source
checks. `git diff --check` passed.
