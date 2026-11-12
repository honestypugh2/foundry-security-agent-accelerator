# Defender signal scope

Defender may provide supported protection, investigation and incident experiences
for an eligible, licensed and connected workload. This repository does not submit
malicious payloads, change Defender settings or claim an incident exists.

An application block or Foundry quality failure does not necessarily generate a
Defender alert. Before presenting integration, verify the exact supported
workload, enabled policies, license, correlation identifiers, observation window
and actual product result in your environment.

Evidence must distinguish "event visible", "alert generated", "incident correlated"
and "action enforced". If any is unavailable, record UNKNOWN or
VERIFICATION_REQUIRED rather than inventing a synthetic Defender response.
Use approved native testing guidance, not real destructive actions.
[Signal boundaries](signal-scope-matrix.md).
