# Correlation model

Each request has a validated UUID correlation ID, preventing path traversal in
per-run artifact names. Each OTel span carries `correlation.id`; the root has mode
and the service resource has name/version. W3C trace context is printed separately
from the application correlation ID.

Audit records include sequence, correlation, event, redacted data, previous hash
and current hash. The action fingerprint binds proposal content, not a model's
summary. Evaluation `case_id` binds normalized results to a dataset case.
Foundry evaluation verifies returned `inputs.case_id` and required metric fields.

Do not equate any of these with a Microsoft Agent Registry ID or Defender/Purview
entity identifier. Cross-product correlation requires actual observed product
IDs, time windows and supported integration—not naming coincidence.
