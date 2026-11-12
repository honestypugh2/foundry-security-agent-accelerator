# APEX session-day alignment validation

Date: 2026-11-12. Branch `main`; baseline commit
`5b090c5f5f26ccc777faddc5c020666bb8a080f5`. Existing dirty changes preserved;
no commit, push or cloud mutation made. The repository is
`foundry-security-agent-accelerator`; machine-specific paths are omitted.

## Executed evidence

| Check | Observed result |
|---|---|
| Baseline `uv run --offline --frozen pytest -q` | 124 passed before changes |
| Frozen dependency restoration | Lock resolved from cache; one notebook wheel cache miss required package download; subsequent frozen restoration passed |
| `uv lock --offline --check` | PASS, 164 resolved lock entries |
| Ruff, strict Pyright, full pytest | PASS: Ruff lint/format, zero Pyright errors/warnings, **141 tests passed** |
| `UV_OFFLINE=1 AZURE_BICEP_CHECK_VERSION=false make validate` | **PASS** on final implementation; **98.49%** measured coverage (CLI remains excluded by existing configuration), **66** security/evaluation tests; both Bicep builds, unsafe gate, source scan, local demo/eval and notebooks |
| Console and module command matrix | Both entry points: doctor, demo, ask, redteam reconciliation, eval gate exit 0 with expected local semantics; both audit spellings verify the actual emitted audit/head |
| Unsafe evidence gate | Expected exit 1 and FAIL/CRITICAL_FAILURE; not a parser error |
| Red-team strict | Expected exit 1 for unsafe/unknown fixture; raw evidence retained |
| Saved agent-status | Offline/SIMULATED label and blocked diagnosis; no SDK call |
| Notebooks | Seven schema/metadata/source-import/output checks; five local notebooks executed in kernels with service sockets and credential acquisition denied; Azure notebooks excluded |
| HTML browser | Offline Chromium PASS: 23 slides, 12 explorers, 54 controls, all 23 mobile slides, zero page errors/network requests |
| Workflow syntax | YAML parsed; read-only permissions, two existing jobs and local notebook step asserted; no production deployment/login job |
| Build | Offline wheel and source distribution built; wheel contains both `fsa` and `foundry_security_accelerator`, no private runtime state |
| Source scan | PASS using existing conservative scanner |
| Dedicated secrets review | detect-secrets 1.5.0, verification disabled; one synthetic dotenv-test false positive manually reviewed; history diff has zero candidates |
| Reachable history review | 20 commits, 217 unique file blobs; no credential/identifier/internal-link/private-path pattern findings; identity/contact metadata still requires owner approval |
| Dependency advisory audit | No known vulnerabilities; editable project skipped; cache deserialization warnings triggered public advisory refresh |
| Dependency licenses | 161 installed distributions declare SPDX/classifier/legacy license metadata; full legal/provenance clearance remains manual |
| Documentation / patch checks | Participant/alignment relative links resolve; `git diff --check` passes |

The application/test/notebook/browser execution paths above are local. Package
downloads and advisory queries are separate tooling network activity, not Azure
execution. Bicep was compiled locally, never deployed; compiler version notices
are not cloud validation.
Local notebook kernels use IPC on Linux and are explicitly shut down after
execution; no long-lived notebook service is left running.

## Scope and remaining blockers

- Existing Azure resources were not reconnected, re-provisioned or changed.
  Earlier live observations in existing documents were preserved, not revalidated.
- Live Azure notebook and read-only whoami/agent-status paths were not invoked
  against a tenant. Mocked contracts do not certify current health or permissions.
- Native registry/activity, Defender/Purview, consent, cloud parity and license
  eligibility remain VERIFICATION_REQUIRED.
- No GitHub runner, protected-check enforcement, production promotion or release
  approval was observed. Workflow parsing is not a hosted CI result.
- PowerShell command syntax is provided, but no Windows/PowerShell execution or
  full timed human presentation was performed.
- These historical checks do not authorize a production release or establish
  confidentiality clearance. See the
  [workshop production disclaimer](participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).
- No alternate retention dataset, persistent approval queue, unsafe runtime config,
  lifecycle publication simulator, or autonomous remote function planner added.

## Files changed for alignment

Existing files integrated, without discarding earlier edits:
`pyproject.toml`, `uv.lock`, `Makefile`, `.github/workflows/validate.yml`,
`.gitignore`, `README.md`, `IMPLEMENTATION_STATUS.md`, `VALIDATION_EVIDENCE.md`;
`config.py`, `cli.py`, `azure_ops.py`, `workflow.py`, `workflow_evaluation.py`,
`agent365/__init__.py`; four existing participant lab guides.

New source: thin `src/fsa/__init__.py` and `__main__.py`;
`scripts/validate_notebooks.py`; `tests/test_compatibility.py`,
`tests/test_notebooks.py`; seven notebooks 00-06.

New documentation: baseline, Cowork inventory, lab/slide alignment, exact commands,
this validation report, Agent 365 status, dry-run checklist; participant index,
troubleshooting/cleanup; root public-release readiness.
The internal alignment baseline distinguishes pre-existing changes; it is
retained for owner review and excluded from the participant release.

## Operational handoff

- Participant commands: [index](participant-lab/README.md).
- Exercise commands and expected outcomes: [local lab](participant-lab/local-fallback.md).
- Resource/identity/consent/governance changes and any publication require
  separately scoped explicit authorization; none was inferred from lab setup.
