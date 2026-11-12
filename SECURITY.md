# Security model and reporting

This is an instructional accelerator, not a production security product.
Report issues privately to the repository owner; do not attach tokens, personal
data, or working exploit payloads to public issues.

The local approver is explicitly synthetic. A production approval service needs
authenticated independent identity, role enforcement, durable issuance and
revocation. The dry-run writer has no business-system connector.

Injection signatures and redaction are defense in depth, not universal detection
or DLP. Trusted entitlement assignment is a caller responsibility. Foundry agent
creation attaches no remote tools; existing agent versions must also be checked.
Audit hash chains require an independently retained head to detect truncation
and an external immutable anchor to prevent full-chain rewriting. A local file
is not a compliance archive. Application traces are not Agent365 ingestion proof.
