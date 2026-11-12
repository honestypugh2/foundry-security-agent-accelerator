# Requirements-to-code gap analysis

Source: VS Code repository implementation spec v0.2.0 (separate review input,
not included in the participant release),
sections 1–17. Comparison baseline: local commit `5185748`, 66 passing tests.
Analysis and remediation: 2026-11-12 UTC.

The reference implementation's reported 133 tests, metrics and slide count are
**not evidence for this repository**. This report does not claim full v0.2
conformance. Existing Python 3.12, frozen dependencies, immutable contracts,
no-tools Foundry boundary and DRY_RUN writer are preserved.

Status vocabulary: **LOCAL** = implemented and exercised locally;
**PARTIAL** = only the stated subset; **DEFERRED** = absent, explicitly identified;
**BLOCKED** = needs independently authorized environmental evidence.
**VERIFIED_LIVE** = the specifically described operation was observed in the
authorized commercial Azure lab, not a production or cross-cloud certification.

## Latest completion evidence

The 16-case same-workflow gate, six persisted scenes and physical 23-slide
presentation are implemented and exercised. The final validation has **124
passing tests**, **98.70%** statement coverage and an offline Chromium pass:
23 slides, 12 explorers, 54 controls, no errors/network requests.

The authorized isolated lab deployed a **new Microsoft Foundry account and
project**, GA model, Search, Content Safety, Logs and Insights. No classic
Foundry hub/workspace was used. All five operator lab grants were read back
at resource scope. Real Search/moderation/pinned-agent runs stopped at
`AWAITING_APPROVAL`, with verified audit heads and no writer call. Seven
correlated application spans were observed in Log Analytics. These observations
do not establish Agent 365, Defender, Purview or Government readiness.
See [validation evidence](VALIDATION_EVIDENCE.md) for precise limitations.

## Critical remediation

| Requirement | Baseline gap | Change | Proof / remaining boundary |
|---|---|---|---|
| §§6–7, AC7–8: agent status | No agent-state reader or diagnosis | [agent_state](src/foundry_security_accelerator/agent_state.py), `fsa azure agent-status [--from-json]`, three synthetic fixtures | [tests](tests/test_agent_state.py): missing fields, disable/legacy interpretation, SDK shapes and exit 2. Real read succeeded; absent optional live states remain unknown |
| §8, AC5–6: seven layers | Only normalized verdict reconciliation | [redteam](src/foundry_security_accelerator/redteam.py), JSON/list/JSONL importer, explicit score polarity, six outcomes/four flags, raw snapshot and reports | [tests](tests/test_redteam.py): exact six-item distribution, unsafe precedence, UNKNOWN fail-closed, strict exit, immutable raw records, original input bytes, malformed/missing evidence |
| §6, AC9: evidence inventory | No `fsa evidence` command | [evidence pack](src/foundry_security_accelerator/evidence.py), ignored `.fsa/reports` default | [tests](tests/test_redteam.py): local/azure status words; saved report does not become product observation |
| §11 INJ-01 | Input shield ran after retrieval | [workflow](src/foundry_security_accelerator/workflow.py): audited input screening before retrieval/model, required input-security span | [tests](tests/test_core.py): denied input makes no retrieval/model call |
| §11 INJ-02 | Retrieved content screened, but no explicit regression proving withholding | Preserve stronger terminate-on-taint behavior, not a bypass/retry path | [test](tests/test_core.py): injected retrieval never reaches model/writer; sensitive text withheld from evidence |
| §11 OUT-01 | Citation instruction not enforced outside model | [security](src/foundry_security_accelerator/security.py): approved-source citation or exact abstention; audited rejection before policy/writer | [tests](tests/test_core.py): absent/unknown provenance denied, existing valid runs preserved |
| AC4 audit diagnostics | Tampering detected but no first-line location | [audit](src/foundry_security_accelerator/audit.py): diagnostic helper; original boolean verifier preserved | [CLI test](tests/test_cli.py): one-character tamper reports line 2. Head mismatch points after retained tail |
| §13 unsafe-must-fail CI | Unit gates existed; no dedicated negative CI job | [workflow](.github/workflows/validate.yml), [verification script](scripts/verify_release_gate.py), `make verify-release-gate` | Checks exit **and** actual critical-failure output; also asserts strict red-team rejection. Workflow not run on GitHub |

Microsoft availability documentation was fetched and the installed SDK
`AgentsOperations.get` signature checked. Important correction: Entra
`instance_identity.status` / `blueprint.status` permit operation with **active**,
not the runtime's **enabled** value. Unknown values never imply full enablement.
[Official source](https://learn.microsoft.com/azure/foundry/control-plane/govern-agent-infrastructure-entra-admin).

## Section-by-section comparison

| Spec section | Status | Current implementation / gap |
|---|---|---|
| 1 Repository | PARTIAL | Tenant-independent original synthetic MIT project. Existing package is `foundry_security_accelerator`, version 0.1.0, Python >=3.12, rather than `src/fsa`/0.2.0/>=3.10. Retained deliberately; no misleading reference-release rebrand |
| 2 Architecture | PARTIAL | Same governed local/Azure workflow, explicit providers, policy/approval/write/audit/OTel; new state/red-team modules. Model deliberately cannot propose function dispatch; no planner/persona/ticket architecture |
| 3 Packages | PARTIAL | Stable Azure SDKs, Foundry evaluation, Monitor/OTLP already present. Frozen all-extras setup preserved; spec's `azure`/`observability`/`eval` extra names and zero-install fallback absent |
| 4 Files | PARTIAL | Equivalent responsibilities in existing modules; new state/redteam fixtures and required extension/setup entry docs added. No broad rename or duplicate runtime |
| 5 Standards | PARTIAL | Strict typed `src`, Ruff, immutable Pydantic boundaries and pure decision functions. Core not converted to dataclasses; Azure imports in existing runtime remain eager; no bare-stdlib runtime |
| 6 CLI | PARTIAL | Existing commands preserved; adds `eval --gate`, `rehearse`, `trace list/show` with trees, unique prefixes and S1–S6 aliases, plus agent-status/redteam/evidence. `demo` remains one workflow, not six scenes; no `doctor`, `ask`, approval queue, audit tail or reset |
| 7 Agent state | LOCAL / VERIFIED_LIVE read | Defensively normalized read-only get succeeded in the lab. Developer/Entra/legacy interpretations tested with synthetic fixtures; missing live fields remain unknown. No real Block/disable propagation tested |
| 8 Red-team reconciliation | LOCAL | Seven layers, outcomes, flags, explicit reviewer polarity, pending sign-off, selected-sample rates; UNKNOWN never pass. Raw dictionary values retained, exact original byte stream saved separately; JSON formatting is not claimed byte-identical |
| 9 Resources | VERIFIED_LIVE scoped lab | [Subscription entry](infra/live.bicep) creates isolated group; [module](infra/main.bicep) parameterizes GA model, Search, Content Safety, monitoring and resource RBAC. ARM validate/what-if and recovery deployment succeeded; five exact resource grants read back. Search-only eastus capacity recovery approved; others eastus2. No azd acceptance or private networking claim |
| 10 Identity | PARTIAL | Trusted caller entitlements, tenant-bound SDK credentials, separate native identity documentation. No persona clearance intersection, OBO, agent-identity provisioning or production caller authentication |
| 11 Security | PARTIAL | See public rule map below. Read-only/no-tools boundary is intentionally stricter than model function calling; no unsafe security-disable switch added |
| 12 Evaluation | LOCAL / PARTIAL service | [16-case dataset](data/evaluation/workflow.jsonl), [six thresholds](data/evaluation/thresholds.toml), [actual workflow runner](src/foundry_security_accelerator/workflow_evaluation.py): measured gate PASS. Nine evidence regressions and six-item reconciliation preserved. Foundry quality SDK adapter exists; live judge blocked on bounded retry controls. No runnable unsafe config or copied reference benchmark |
| 13 CI/CD | PARTIAL | Pinned local validation/advisory/SBOM workflow plus negative-gate job. No zero-install, CodeQL/gitleaks/dependency-review or preview cloud-eval workflow. No remote runner execution claimed |
| 14 Docs | PARTIAL | Detailed existing architecture/labs/security/cloud docs and new exact extension/setup entry pages. Product/source limitations explicit. Remaining reference filenames/Path A bare-Python instructions not fabricated |
| 15 Slides | LOCAL main deck / PARTIAL appendices | **23 substantive slides** in exact requested order with 45-minute notes, six-plane architecture and all 12 explorers retained; browser-verified desktop/mobile. Reference A1–A17 appendix slides not shipped |
| 16 Acceptance | PARTIAL | Explicit criterion table below; actual test/coverage results in validation evidence |
| 17 Open issues | PARTIAL / DEFERRED | New Foundry workflow and scoped RBAC observed; no real blocked-agent error, Government parity, azd acceptance or GitHub runner. New CLI does not introduce the reference doctor's false-ready behavior |

## Public security rule mapping

These are spec IDs, not renumbered controls or proof of a reference runtime.

| Rule | Status / enforcing code | Focused evidence or remaining gap |
|---|---|---|
| ID-01 | PARTIAL: typed subject/entitlements before workflow | [core tests](tests/test_core.py); production authentication/persona resolution absent |
| INJ-01 | LOCAL: audited pre-retrieval input shield | Input-order regression |
| INJ-02 | LOCAL adaptation: reject untrusted retrieved content before model | Termination rather than continue-tainted quarantine; no write on failure |
| DATA-01 | PARTIAL: Search pre-ranking entitlement filter, secondary row validation | [Azure tests](tests/test_azure.py); no classification-clearance model or `get_policy_section` |
| DATA-02 | LOCAL: untrusted evidence delimiters in model input | [workflow](src/foundry_security_accelerator/workflow.py); sources remain untrusted |
| TOOL-01 | LOCAL: closed read-only registry and pinned agent with no remote tools | [core](tests/test_core.py), [Azure](tests/test_azure.py); stronger than a function-tool allowlist |
| TOOL-02 | LOCAL within supplied tools: typed arguments and default-deny egress helper | No network-capable function tool is exposed; [tests](tests/test_core.py) |
| TOOL-03 | LOCAL: exact independent expiring approval, authority/scope binding | [approval/writer tests](tests/test_core.py); production authenticated approver absent |
| OUT-01 | LOCAL: approved-source citation or explicit abstention | No-citation/unknown-source output cannot reach writer. Citations are provenance, not factual entailment proof |
| OUT-02 | PARTIAL: synthetic-only input schema, entitlement trimming, redaction | No general Confidential-content classifier or Purview DLP connector; not advertised as one |

## Acceptance criteria traceability

| Criterion | Status | Evidence / precise gap |
|---|---|---|
| AC1 bare Python S1–S6 | PARTIAL | All six persisted scenes exercised through `fsa rehearse`; dependency-free Python 3.10 / `python -m fsa` remains deferred |
| AC2 stdlib tests / coverage | PARTIAL | pytest, strict typing and >=85% required-module coverage; no stdlib runner; do not copy reference test count |
| AC3 safe/unsafe config metrics | PARTIAL | Safe 16-case actual-workflow gate PASS: task16/16, tools16/16, citations8/8, attacks0/8, violations0, case-canary leaks0. Tests prove threshold failures reject; unsafe-evidence release rejection preserved. No unsafe runtime or claimed reference 0.875 ASR |
| AC4 tamper and first broken line | LOCAL adaptation | Existing `audit-verify` command, now first-line diagnostic; boolean API retained |
| AC5 exact six-item reconciliation | LOCAL | Exact 5/6 raw ASR, 1/6 unsafe rate, specified distribution and strict exits; no population inference |
| AC6 raw preservation | LOCAL | Deep copied raw fields + byte-for-byte original input snapshot; formatting/order preserved in snapshot, not reserialized JSON |
| AC7 fixture status / missing states | LOCAL | Three fixtures, missing/unknown fields, Entra active/disabled, legacy precedence |
| AC8 live read/error boundary | PARTIAL / VERIFIED_LIVE read | Real SDK get succeeded; status exit 2 tested for configuration/service errors. Core SDK dependencies remain required; no missing-all-Azure-packages/zero-install CLI guarantee |
| AC9 evidence rows | LOCAL | Exact Agent 365/red-team rows; azure registry NOT CHECKED HERE; local NOT OBSERVED IN THIS MODE |
| AC10 policy before function execution | LOCAL stricter boundary | No model-directed function execution permitted; application registry rejects writer; deterministic approval/policy at DRY_RUN writer |
| AC11 no private data | LOCAL limited scan | Public original synthetic fixtures and tenant-neutral templates. Scanner allows only five exact public built-in role IDs, rejects arbitrary IDs; private configuration/results remain ignored. Not gitleaks or full release review |
| AC12 no synthetic platform signals | LOCAL | Status fixtures explicitly SIMULATED/offline; red-team data is synthetic action evidence, not Defender/Agent 365/Purview signals |
| AC13 live validation | PARTIAL / VERIFIED_LIVE workflow | Authorized new resource/project/model provisioning, prompt-agent creation/read, Search/moderation/invocation, resource role verification and correlated Monitor rows. No `ask` alias, blocked-agent test, cloud judge result, publication, consent or native product validation |

## Remaining work, ordered by consequence

1. **Production acceptance blockers:** authenticated caller/entitlement binding,
   independent human-approver authentication, scoped protected evidence storage,
   native data classification/DLP and authorized cloud/RBAC/network verification.
2. **Behavioral conformance gaps:** persona clearance model and persistent
   approval queue. The 16-case metrics suite is closed. Do not introduce a
   runnable unsafe write configuration to imitate benchmark numbers.
3. **Participant compatibility:** choose a separately approved migration plan for
   bare-stdlib Python >=3.10/package compatibility and remaining CLI names.
   Trace aliases and six scenes are closed. A second ungoverned runtime would
   invalidate shared controls.
4. **Presentation/packaging:** main 23-slide deck closed; appendix expansion,
   reference filename aliases, timed human delivery and release review remain.
5. **Remote validation:** service quality evaluation is authorized for up to four
   judge calls but not run: the installed chat evaluator internally retries up to
   ten times, beyond that bound. Resolve supported bounded judge configuration
   before submission. Publishing, native integrations and additional mutations
   still need separate authorization; no push/publication performed.

No validated modules were discarded. New analysis/reporting runs offline; the
live status path is a separate read-only SDK operation. See
[validation evidence](VALIDATION_EVIDENCE.md) and
[participant learning paths](docs/participant-lab/README.md).
