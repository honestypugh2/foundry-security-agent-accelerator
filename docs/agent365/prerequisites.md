# Agent 365 prerequisites

Before any integration exercise, separately verify:

- Intended tenant/cloud, Foundry account/project and eligible agent type.
- Applicable Agent 365 license and documented tenant consent.
- Named owner/sponsor responsibilities and least-privilege operator access.
- Supported publication/connection path and current product availability.
- Data-collection settings, telemetry destinations, retention and data handling.
- Defender/Purview licensing and native integration prerequisites, if in scope.

```bash
make agent365-preflight
make agent365-status
# Only for an authorized read of the documented preview account fields:
uv run fsa agent365 status --preview-api
```

Default settings inspection does not opt into preview. A prerequisite checklist
is not a successful live connection. Missing permission/license/observation must
remain an explicit blocker. [Architecture and Microsoft sources](integration-architecture.md).
