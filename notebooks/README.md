# Workshop notebooks

## Start here

From the repository root, in Bash or PowerShell:

```text
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
```

Use Python 3.12. Open the repository folder in VS Code with the Python and
Jupyter extensions. Open a notebook, choose **Select Kernel -> Python
Environments -> the repository `.venv` interpreter**, then run cells in order.
The generic kernel display name is not proof that the right interpreter is
selected; notebook 00 checks it. Installation needs package access once.

## Core path: local and credential-free

| Order | Notebook | What to observe |
|---|---|---|
| 1 | [00 Setup](00_environment_setup.ipynb) | Package/kernel checks pass; Azure NOT_CHECKED |
| 2 | [02 Protect](02_protect_identity_and_tools.ipynb) | Policy, access and injection denials; DRY_RUN approvals |
| 3 | [03 Prove](03_prove_evaluations_and_redteam.ipynb) | Safe PASS; deliberately unsafe FAIL; evidence reconciliation |
| 4 | [04 Operate](04_operate_traces_and_audit.ipynb) | Local trace inspection and audit-copy tamper rejection |

[06 Local walkthrough](06_local_fallback.ipynb) is a consolidated alternative
after setup, including local lifecycle simulation.
These five local notebooks support Run All; notebook 02's optional Azure branch
is OFF by default. Local execution must not acquire credentials or use services.
Restart the kernel before repeating a lab. Keep the synthetic/DRY_RUN labels.

## Optional cloud extensions: run cell by cell

- [01 Azure Live](01_foundry_agent_live.ipynb): requires your own configured,
  authorized existing resources. Consent allows at most two model calls plus
  the documented service checks per invocation; repeating it repeats cost.
  IQ discovery has separate consent and does not prove retrieval.
- [05 Agent 365](05_agent365_extension.ipynb): its first code cell is offline.
  The optional account-setting read asks for explicit authorization. Portal
  registry/activity/Defender observations are independent acceptance tasks.
- Notebook 02's live section runs only if you deliberately enable its flag and
  supply the required authorization.

Do not use unattended Run All for 01/05. Declining consent raises PermissionError
by design. Missing telemetry can produce PARTIAL and an assertion in 01; stop
and inspect the sanitized results rather than bypassing the check. Missing IQ
configuration is a real gap, not evidence that the notebook itself is broken.
No cloud notebook provisions or publishes resources.

## Validation and help

The local validator checks all seven notebook contracts/imports, executes only
the five allowlisted local notebooks under network/credential denial, and
keeps source outputs empty:

```text
uv run python scripts/validate_notebooks.py --execute-local
```

Azure notebooks are not executed in PR CI. Passing local validation does not
establish live cloud success.

See the [participant guide](../docs/participant-lab/README.md),
[Azure prerequisites](../docs/participant-lab/azure-live-lab.md),
[troubleshooting](../docs/participant-lab/troubleshooting.md), and
[cleanup](../docs/participant-lab/cleanup.md).
Clear all outputs before sharing; `.fsa`, `artifacts` and private `.env` must
remain local.

**Workshop only, not production or WAF certification.** Read the
[production/Well-Architected Framework disclaimer](../docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).
