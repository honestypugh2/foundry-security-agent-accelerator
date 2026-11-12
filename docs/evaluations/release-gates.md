# Fail-closed release gates

Reconcile each case first, retaining raw records. Across required case results:
FAIL blocks; then INSUFFICIENT_EVIDENCE blocks; then REVIEW_REQUIRED blocks;
NOT_EVALUATED is not success. Empty required results are insufficient.
Only all-required PASS permits the bounded release gate to pass.

```bash
uv run fsa evaluate --mode local
uv run fsa gate path/to/normalized-evaluation-evidence.json
uv run pytest -m "security or evaluation"
```

The gate input is the typed EvaluationEvidence contract, not arbitrary service
JSON or the local regression aggregate. Commands return nonzero for non-PASS.
Foundry service evaluation reports quality independently and never invokes the
security release gate on its own. Production release and business-action
authorization remain distinct.
