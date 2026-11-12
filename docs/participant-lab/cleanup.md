# Cleanup and output hygiene

No participant notebook automatically provisions, deletes, publishes or modifies
Azure resources, agents, identities, logging, consent, Defender or Purview.
Existing services may continue to incur cost. Ask the resource owner to review
the exact resources and dependencies before separately authorizing changes.
Never delete a shared resource group.

Local run artifacts are under ignored `.fsa/` or `artifacts/`. Retain original
audit files and an independent head until review; tamper only with a copy.
Delete only the particular run directory you created after resolving its path,
not the repository, home, state root or shared evidence.

Before sharing notebooks, use VS Code **Clear All Outputs**, save, then:

```text
uv run python scripts/validate_notebooks.py
```

It rejects execution counts, outputs and embedded attachments. It is not a
substitute for manual confidentiality review of Markdown, screenshots and
source. Never commit `.env`, private observation records, credential material,
live outputs or generated deployment state. Do not copy presenter-only Cowork
material into a participant distribution.
