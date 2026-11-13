# Deterministic offline lab

Choose this explicit fallback when the Azure-first workshop prerequisites are
unavailable. An Azure failure must be retained as a failure, not rewritten as
local success. Notebook 06 stays local even in an otherwise Azure Live session.

After installing dependencies once, local execution requires no Azure connection.
Use Python 3.12 and the frozen lock; no Node.js is required.

Preferred guide: [06 local notebook](../../notebooks/06_local_fallback.ipynb).
There is no zero-install/standard-library-only path. Bash and PowerShell can
both use the following module-compatible commands without shell activation:

```text
uv sync --frozen --all-extras --dev
uv run python -m fsa doctor
uv run python -m fsa ask "Explain synthetic equipment policy." --as analyst
uv run python -m fsa demo
uv run python -m fsa eval --gate
uv run python -m fsa redteam reconcile
uv run python -m fsa rehearse
uv run python -m fsa trace show S4
```

Continue with [02 Protect](../../notebooks/02_protect_identity_and_tools.ipynb),
[03 Prove](../../notebooks/03_prove_evaluations_and_redteam.ipynb), and
[04 Operate](../../notebooks/04_operate_traces_and_audit.ipynb).
Expected: doctor reports local/configuration-only; the equipment ask awaits
approval; default local demo runs all six synthetic presentation scenes.
`ask --as guest` is denied; analyst/hr-investigator use synthetic employee
entitlements, not real identity authentication. Presentation questions use a
separate fictional retention/vendor/ticket/HR corpus, not legal guidance.
Local mode excludes private dotenv and
remote-export flags. For a DRY_RUN receipt explicitly use local `demo --demo-approval`.
For `audit verify`, supply the printed path and independently retained head.
See [troubleshooting](troubleshooting.md) and [cleanup](cleanup.md).

```bash
uv sync --frozen --all-extras --dev
uv run fsa demo --mode local --demo-approval
uv run fsa evaluate
uv run fsa eval --gate
uv run fsa rehearse
uv run fsa trace list
uv run fsa trace show S4
uv run fsa trace-check
uv run pytest -m "security or evaluation"
```

These same commands work in PowerShell. `demo --profile equipment` without
`--demo-approval` stops with `AWAITING_APPROVAL`. With approval, a synthetic independent reviewer permits
only a DRY_RUN receipt. Do not describe that reviewer as a production human
identity service.

Default local `demo` runs the presentation's six scenarios; `rehearse` retains
the equipment-workflow regression scenes under ignored `.fsa/`. `trace show S4`
prefers the latest presentation manifest when available: vendor retrieval,
indirect-injection quarantine and denied export. Without a presentation manifest
it resolves the equipment rehearsal's different S4 unsupported-export request.
`eval --gate` measures the 16-case equipment workflow plus presentation checks;
the separately selected unsafe configuration measures only an in-memory local
sandbox. Any breach or incomplete evidence blocks the corresponding gate.

Inspect the printed audit and spans paths. Retain the audit head independently,
then verify the audit with `uv run fsa audit-verify PATH --expected-head HEAD`.
Change one byte in a **copy** to demonstrate rejection; never alter retained
original evidence. A valid chain without an external head cannot prove absence
of tail truncation or complete rewriting.

Local regression PASS means the analyzer recognized expected PASS/FAIL/review/
missing-evidence cases. It does not mean every adversarial case is safe for release.
No local trace, fixture or receipt is Microsoft service evidence.
