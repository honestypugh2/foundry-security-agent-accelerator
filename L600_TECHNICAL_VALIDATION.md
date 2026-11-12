# L600 technical validation

## Authority and effect boundaries

The application—not an LLM—constructs the typed action proposal. Retrieved content
is untrusted. Foundry invocation verifies the pinned prompt-agent model and
absence of remote tools. Only the closed application registry executes read-only
tools. The writer validates exact independent authority-issued, expiring approval
and only records an idempotent DRY_RUN receipt.

Local mode rejects injected external providers and remote exporters. Azure mode
uses explicit SDK boundaries; errors cannot select a silent synthetic fallback.
Caller authentication and production approver identity remain unimplemented.

## Evaluation semantics

Raw records, normalized verdicts, reconciled outcomes and human adjudication
remain distinct. Confirmed critical unsafe execution and deterministic failure
outrank safe final-answer text. Critical model disagreement requires review;
missing/errored/incompatible required tools/spans/verdicts block release.

Foundry SDK quality judging requires explicitly authorized synthetic data,
relevance/groundedness metrics, finite 1–5 scores and exact unique case coverage.
It preserves the raw result and never equates quality PASS with security release.

The separate red-team importer preserves original input bytes and deep-copied
raw fields. Seven layers distinguish evaluator, response, invocation,
authorization, execution, downstream evidence and candidate adjudication.
Missing evidence remains UNKNOWN; strict mode rejects unknown/unsafe cases.
Strict red-team filtering is not the production release gate or human sign-off.

## Availability interpretation

`azure agent-status` uses only the installed SDK's read-only `agents.get`.
Saved JSON always carries offline provenance labeling. Operational enablement,
developer configuration and Entra identity/blueprint states are independent.
Missing fields never establish full enablement; an enabled runtime with disabled
Entra state produces a legacy warning. No disable, Block or publication occurs.
A real read succeeded in the isolated lab; optional missing fields remain
unknown. Block/disable/legacy behavior is fixture-tested, not a live mutation.

## Identity and telemetry

Entra SDK token acquisition is configured per cloud and guarded for the selected
tenant. Decoding the tenant claim is not independent JWT signature authentication.
Each OTel span carries application correlation; batch delivery is tracked
separately from ingestion. Export failure fails the command while local evidence
remains. Scoped read-only Log Analytics rows prove only application telemetry
within that query's time/window, never Agent 365/Defender/Purview coverage.
The installed Monitor exporter now receives its supported `timeout` and the
per-run tracer provider without replacing the process-global provider. Live
delivery succeeded, and a separate one-hour correlation query returned seven
application spans. The real-constructor regression prevents the duplicate
`connection_timeout` keyword failure observed during smoke testing.

Hash linkage detects mutation, and retained expected heads detect truncation.
Complete rewriting requires protected external anchoring to detect. Supplied
stage checks do not prove absence of uninstrumented actions.

## Native Microsoft ownership and maturity

Foundry owns workload execution; Entra identity; Azure resource/network controls;
Agent 365 applicable inventory/lifecycle/activity; Defender security investigation;
Purview native data protection/audit. No unified fictional authority is introduced.
SDK stability, feature GA/preview status, cloud availability and observed service
results are separate dimensions.

## Validation and release boundary

The [measured evidence](VALIDATION_EVIDENCE.md) covers deterministic invariants,
installed SDK contracts, Bicep syntax and actual offline browser interactions.
Required module coverage exceeds 85% individually. It does not certify tenant
readiness, government feature support, live service behavior, production
authentication, DLP, immutable evidence storage or enterprise approval.

The 16-case local workflow suite measures six explicit metrics against retained
thresholds and evidence; missing action evidence cannot be counted as a block.
Its zero attack/canary counts apply only to selected cases. Six local scenes
retain original heads and a deliberately tampered copy; the 23-slide browser
check is separate. A real Azure workflow reached `AWAITING_APPROVAL` with no
writer call. ARM provisioning and five resource-scoped grants were read back.
These are scoped live observations, not inference from Bicep or synthetic tests.

Foundry quality-judge evaluation remains blocked despite authorization for four
calls: the installed chat-model evaluator has an internal ten-retry path.
No judge submission was made without a supported way to honor the call bound.

Production/live acceptance therefore remains **VERIFICATION_REQUIRED** and cannot
be unlocked by local regression PASS alone.
