# Advanced threats and regression evidence

Run `uv run pytest -m "security or evaluation"` without cloud credentials.

- Cross-tenant confusion: explicit authority/audience/tenant guard; token decoding
  is a scope guard, not independent token authentication.
- Entitlement injection: apostrophes escaped in equality filters; empty
  entitlements do not query Search; unauthorized returned rows fail.
- Tool-output laundering: model summaries cannot create tools or authorize writes.
- Proposal mutation/replay: exact content fingerprint and expiring authority-issued
  approval; idempotent DRY_RUN receipt.
- Approval self-grant: requester cannot act as independent approver; synthetic
  approver is unavailable in Azure workflow mode.
- Evaluator laundering: safe final response cannot erase confirmed unsafe
  execution; conflicting critical model verdicts require review.
- Evidence substitution: judge rows must map exactly to unique dataset case IDs.
- Telemetry loss: failed export fails the command; missing stages block the gate.
- Cross-cloud export: endpoint validation and explicit exporter selection.

Tests establish these bounded invariants, not exhaustive adversarial robustness.
Uninstrumented side effects, compromised process/host and authenticated approver
compromise require additional platform controls and production design review.
