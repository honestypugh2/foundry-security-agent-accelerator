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

## Egress and network boundaries

Local mode does not construct remote providers/exporters; tests deny socket
connections and DefaultAzureCredential token acquisition. Azure mode validates
cloud-specific HTTPS service endpoints and never silently falls back.
The application allowlist is not a host firewall or Web Application Firewall.
Production also needs appropriate network isolation, DNS/proxy restrictions,
workload identity, credential controls and destination review.

OTLP permits HTTPS or explicitly selected loopback HTTP outside local mode.
Local mode rejects remote export even when configured. Review telemetry content
before enabling exporters; service evaluation submits synthetic content only
with explicit authorization. Compiled teaching Bicep is not proof of isolation.

## MCP and delegation extensions

The supplied prompt agent has no remote tools or MCP registration. Its read-only
registry is application-controlled, not model-dispatched. Before adding MCP,
review server inventory, authenticated transport, scoped credentials, schemas,
data classification, egress and tool-description changes. Treat descriptions
and results as untrusted. Do not add generic shell/admin tools or writer access
to reproduce a lab; reject unauthorized calls before invocation.

This is not an autonomous multi-agent network. A delegate must retain the
authenticated caller scope, explicit task, classification, tools/egress budget
and correlation context. It cannot widen entitlements, approve itself, alter
evidence or dispatch the writer. Preserve each action's evidence; parent prose
cannot turn missing child results into success. No remote MCP or deployed
multi-agent validation is claimed.

## Evidence assurance

Preserve raw observation, normalized interpretation, reconciled outcome, human
adjudication and release decision separately. Never rewrite a failing raw record.
An independent audit head detects truncation, but an attacker controlling both
the entire file and trusted head defeats local assurance. Production needs
protected append-only storage and external anchoring, not deployed here.

Trace checks cover supplied stage names, not all actions. Export success is not
ingestion; queried rows establish only that workspace/time/application scope.
Operator attestations establish documented scope/freshness, not authenticity.
Missing required evidence is INSUFFICIENT_EVIDENCE; unsafe execution is FAIL.
See the [evaluation guide](../evaluations/framework.md).
