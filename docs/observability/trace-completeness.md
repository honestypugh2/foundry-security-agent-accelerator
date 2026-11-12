# Trace completeness and delivery

Required governed stages: input-security, retrieve, security, tool, model, policy, approval,
writer. `trace-check` evaluates actual JSONL span names, not prose in a model
response. An unapproved Azure run correctly lacks approval/writer spans and
cannot pass the full-write completeness gate.

```bash
uv run fsa trace-check --trace artifacts/<correlation-id>.spans.jsonl
```

The check is structural coverage within the supplied evidence file. It does not
authenticate the file or prove ingestion, absence of uninstrumented actions,
or Microsoft-product coverage. Correlate with the audit chain and independently
retained head. Azure Log Analytics observations supplement—not replace—these
application evidence checks.

Missing required stage -> INSUFFICIENT_EVIDENCE. Export failure -> command failure
with local artifacts retained. Empty/partial workspace query -> INSUFFICIENT_EVIDENCE.
