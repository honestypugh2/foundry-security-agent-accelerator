# Multi-agent delegation

The runtime is deliberately a single bounded prompt-agent workflow, not an
autonomous multi-agent system. Delegation validation is a reusable local control;
it does not imply a deployed specialist-agent network.

Any extension must carry the authenticated caller scope, explicit task boundary,
data classification, allowed tools/egress, time/resource budget and correlation
context. A delegate cannot widen entitlements, grant itself approval, alter
evidence or dispatch the writer.

Require direct evidence for delegated actions and preserve individual outcomes.
Parent-agent prose cannot convert a missing child result into success.
Use exact independent approval for side effects, not a parent model's
"approved" message. [Threat model](advanced-threat-model.md).
