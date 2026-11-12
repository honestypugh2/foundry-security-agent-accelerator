# Evidence assurance

Preserve separate layers: raw observation, normalized interpretation, reconciled
outcome, human adjudication and final release decision. Never rewrite a failing
raw record to match a desired model verdict.

Audit verification detects changed records and, when the expected head is retained
independently, truncation. An attacker able to rewrite both the entire file and
the trusted head defeats local assurance. Production needs protected append-only
storage and external anchoring; these are not deployed here.

Trace completeness checks supplied stage names, not all possible actions.
Exporter success does not prove ingestion. Workspace rows establish only the
queried application telemetry scope. Operator attestations establish documented
scope/freshness, not remote authenticity.

Missing required evidence is INSUFFICIENT_EVIDENCE. Confirmed unsafe execution
is FAIL even when the final answer looks safe. [Verdict semantics](../evaluations/verdict-semantics.md).
