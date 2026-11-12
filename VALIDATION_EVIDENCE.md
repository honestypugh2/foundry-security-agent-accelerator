# Validation evidence

## Session-day alignment addendum

Fresh baseline: 124 tests passed before edits. Current CLI compatibility,
package-backed notebooks, local kernel execution, source/history review and
exact command outcomes are recorded in
[APEX validation results](docs/APEX_VALIDATION_RESULTS.md).
Final alignment run: **141 tests passed**, **98.49%** measured coverage,
**66** security/evaluation tests; required `make validate` passed.
Seven notebooks are output-free; only local notebooks execute in CI. The live
Azure and native-platform observations below are retained historical records,
not new observations made by this alignment.
These historical checks do not authorize production deployment; see the
[production/WAF disclaimer](docs/participant-lab/README.md#production-and-well-architected-framework-waf-disclaimer).

Date: **2026-11-12 UTC**. Environment: Linux aarch64; Python **3.12.3**,
uv **0.12.23**, Git **2.43.0**, Azure CLI **2.90.0**, Bicep **0.48.1**.
This report distinguishes executed local checks from unperformed service checks.

## Executed

| Check | Actual result |
|---|---|
| `UV_OFFLINE=1 uv sync --frozen --all-extras --dev` | PASS; 132 installed packages checked without network |
| Ruff lint / format | PASS |
| Strict Pyright | PASS; zero errors/warnings |
| Full pytest suite | PASS; 124 tests; validated earlier behavior retained |
| Security/evaluation selection | PASS; 66 passed, 58 deselected |
| Coverage | 98.70%: 1294/1311 measured statements; CLI excluded by existing coverage configuration |
| Local synthetic regression | PASS; nine expected classifications, including FAIL/review/missing evidence |
| `uv run fsa eval --gate` | PASS; 16 actual same-workflow cases, six measured thresholds, retained dataset/threshold hashes and per-run evidence |
| Workflow metrics | Task16/16, exact tools16/16, citations8/8 observed responses, attack success0/8 selected attacks, policy violations0, case-canary leaks0 |
| `uv run fsa rehearse`; `uv run fsa trace show S4` | PASS; all six persisted scenes, original audit verified, tampered copy first broken line2, S4 has no writer |
| Local governed workflow | DRY_RUN, complete required stages, LOCAL_ONLY telemetry |
| Bicep compilation | PASS; not Azure acceptance or provisioning |
| Source-pattern scan | PASS; not a substitute for confidentiality review |
| `uv run pip-audit --skip-editable` | No known vulnerabilities; editable project skipped |
| `UV_OFFLINE=1 uv build --out-dir artifacts/dist` | Wheel/source distribution built; new state/red-team/evidence modules present; private runtime state excluded |
| CycloneDX SBOM | Generated with all extras/groups; 133 components, including evaluation/Monitor/query/OTLP boundaries |
| Actual offline Chromium interactions | PASS; 23 substantive slides, 12 explorers, 54 controls, all23 mobile slides, zero page errors/network requests |
| Negative release gate | PASS; unsafe execution yields exit 1 and CRITICAL_FAILURE, not an unrelated CLI error |
| Synthetic seven-layer reconciliation CLI | Exact six-item distribution; raw ASR 5/6, confirmed unsafe 1/6; strict exits 1 |
| Saved agent-state CLI | Legacy fixture prints offline/SIMULATED warning, all fields, distinct legacy diagnosis |
| Evidence inventory CLI | Writes scoped report without live/product validation claims |
| Documentation relative links | PASS; requirements report, matrix and documentation targets resolve |

Browser checks exercise navigation, theme, presenter notes, timer, keyboard help,
print, portal search/tabs, architecture, troubleshooting, clipboard feedback and
mobile viewport. Async clipboard/timer assertions wait for observable results.

## Exact required module coverage

| Required module | Measured statement coverage |
|---|---|
| Configuration | 100% |
| Security | 100% |
| Policy | 100% |
| Approval | 100% |
| Writer | 96% |
| Audit | 100% |
| Evaluation | 100% |
| Workflow orchestration | 95% |
| Agent 365 verification | 100% |
| New Foundry agent-state interpretation | 100% |
| New red-team reconciliation | 100% |
| New evidence-pack inventory | 100% |
| Actual workflow evaluation | 98% |
| Persisted rehearsal / trace reader | 99% |

All specified modules individually exceed 85%. This is statement coverage,
not branch completeness, exhaustive adversarial testing or a production guarantee.
SDK-boundary tests inject clients/evaluators/exporters. Test sockets and default
credential token acquisition are denied; private `.env` and FSA environment
variables are excluded from test settings.

## Executed live: authorized isolated commercial Azure lab

| Operation | Observation / boundary |
|---|---|
| Provisioning | Actual ARM validate/what-if and recovery deployment Succeeded; new Foundry account (`AIServices`, project management enabled), project, GA model, Search, Content Safety, Logs/Insights |
| Foundry generation | **New Foundry only**; project type `Microsoft.CognitiveServices/accounts/projects`, project managed identity; no classic hub/workspace |
| Model | GA `gpt-5-mini`, version `2025-08-07`, GlobalStandard capacity10; default content filter policy retained |
| Regions | Foundry/model/Safety/monitoring eastus2; Search-only eastus recovery explicitly approved after eastus2 capacity failure |
| Least privilege | Five lab operator assignments read back at exact resource scopes, no lab resource-group grant; four own overbroad grants replaced with explicit approval |
| Retrieval / moderation | Original two-document synthetic Search index populated; employee entitlement filter verified; real Content Safety requests in the shared workflow |
| Agent | Real create/read; exact version pinned; no remote tools; expected model checked. Project token scope corrected to `https://ai.azure.com/.default`; response body corrected to `agent_reference` |
| Shared workflow | Two successful synthetic invocations observed; `AWAITING_APPROVAL`, approved-source citations, verified retained audit heads, no writer call |
| Monitor export | Actual exporter delivery succeeded; supported timeout/per-run provider binding covered by a real installed-exporter construction regression |
| Monitor ingestion | Separate read-only one-hour query returned **7** spans for the monitored workflow correlation; application telemetry only |

Raw ARM, scoped-role, agent, run/audit/trace and query evidence remains in ignored
operator state, not in the participant package. Public reports intentionally omit
private tenant/subscription/principal values and deployment endpoints. Live SDK
requests were separate from deterministic socket-blocked tests.

## Evidence limitations and explicit blockers

- Foundry quality judge: authorization received for at most four judge-model calls,
  but **no submission made**. Installed chat-evaluator transport can internally
  retry up to ten times; the adapter cannot yet guarantee that bound. The checked-in
  smoke dataset contains one case; the proposed second case is the real synthetic
  workflow response, not an already-run two-case evaluation.
- The Quota CLI was blocked by unregistered Microsoft.Quota; provider-specific
  usage and target ARM checks were used. No provider registration or quota
  increase was performed. No cloud cleanup or enforced spending cap.
- Agent 365 preview account fields are tested against mocked documented output;
  no registry/activity, Defender or Purview product observation was made.
- Package/API compatibility and public documentation are not live service proof.
  Stable distributions may contain beta-versioned exporter internals, disclosed
  in the product ledger.
- Azure SDK GitHub API source access encountered organization SAML enforcement;
  official Learn references and installed signatures were used without bypass.
- No full timed human presentation or PowerShell execution was rehearsed.
  Cloud commands with operator-specific placeholders were not executed.
- Provisioning initially hit Search capacity and account/project operation
  conflict; reviewed regional recovery/ordering succeeded. Bicep null-asserted
  role scopes compiled too broadly; corrected scopes were redeployed and read
  back. Compiler-scope regression covers all five roles.
- Dependency audit queries public advisory metadata; it is separate from the
  network-free application/test/browser paths.
- Private configuration, local receipts, raw evidence, builds and SBOM remain
  ignored. No push/publication, tenant consent or existing-identity changes.
  New lab resource managed identities and scoped roles were explicitly approved.

Reproduce: frozen sync, `make validate`, optional
`UV_OFFLINE=1 uv run --with playwright python scripts/validate_html_browser.py`.
Playwright/Chromium must already be installed for an offline browser run.

## v0.2 specification comparison and new verification

The [requirements gap analysis](REQUIREMENTS_GAP_ANALYSIS.md) covers every spec
section and acceptance criterion. Its baseline is commit `5185748`; the current
124-test result is measured here, **not the reference implementation's reported
133 tests**. Existing package/Python/dependency and DRY_RUN boundaries are retained.

New tests verify:

- Actual installed SDK `AgentDetails` normalization; status uses only read-only
  `agents.get`. Camel/snake/attribute/as_dict, missing states,
  developer disable, identity/blueprint disable and legacy precedence are covered.
- `--from-json` never calls the SDK and always prints offline/SIMULATED provenance;
  invalid JSON and live boundary errors yield status exit 2 without secret details.
- Seven raw/action/adjudication layers, exact synthetic outcome counts and strict
  rejection; unknown evidence, empty details, nonfinite JSON, unconfirmed score
  polarity, conflicting verdicts and mismatched execution tools never become pass.
- Original raw input bytes retained; raw dictionaries deep copied; identical
  reruns accepted but different evidence cannot overwrite retained reports.
- Input screening precedes retrieval/model; retrieved injected text never reaches
  the model/writer; unknown or absent output citations stop before policy/write.
- A one-character audit tamper reports the first broken line while the existing
  boolean verifier API remains unchanged.

The local-only presentation-to-code matrix maps all 23 physical slides to
actual code/tests/known gaps. Browser interaction
counts are measured here, not copied from the reference.
The new negative CI job was exercised locally through its verification command
and equivalent synthetic CLI checks; **GitHub runner execution is unverified**.

Remaining gaps include the bare-stdlib Python >=3.10 runtime, persona/clearance
planner, persistent approval queue, several reference CLI commands and reference
appendices. The 16-case workflow metrics, six scenes and 23-slide main deck are
closed. Live cloud judge, native Agent 365/Defender/Purview observations and
Government parity remain unverified. No full v0.2 conformance is claimed.
