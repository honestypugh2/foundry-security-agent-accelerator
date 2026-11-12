# Cowork participant-lab alignment

Source root and classifications are retained in the internal artifact inventory,
excluded from the participant release.
Only objectives and exercise structure were reused; prose/code/outputs were not
copied from Cowork. Actual current validation is in
[results](APEX_VALIDATION_RESULTS.md), not inherited from source captures.

| Cowork source | Objective | Existing implementation | Correct command | Notebook | Azure / Agent 365 | Expected result | Actual validation / status | Required correction |
|---|---|---|---|---|---|---|---|---|
| `04_Participant_Lab/Azure_Live_Lab.md` | Governed real request | `agent`, `workflow`, `retrieval`, `security` | `uv run python -m fsa --mode azure ask "Explain synthetic equipment policy." --as analyst` | [01](../notebooks/01_foundry_agent_live.ipynb) | Azure yes / A365 no | AWAITING_APPROVAL, audit, no writer | SDK contracts tested; no fresh live execution / ALIGNED_WITH_CAVEAT | Existing project only; Python 3.12; real extras; pinned no-tools agent; no provisioning |
| `04_Participant_Lab/Local_Fallback_Lab.md` | Offline controls and evidence | `workflow`, `rehearsal`, `workflow_evaluation`, `audit` | `uv run python -m fsa rehearse`; `uv run python -m fsa eval --gate` | [06](../notebooks/06_local_fallback.ipynb) | No / no | Six retained scenes, 16-case local gate PASS | Kernel execution with service network denied / ALIGNED_WITH_CAVEAT | Preinstall deps; no bare-stdlib path; one-run demo vs six-scene rehearsal; no approvals queue |
| `04_Participant_Lab/Agent365_Extension_Lab.md` | Separate governance observations | `agent365`, `agent_state` | `uv run python -m fsa agent365 preflight`; saved `azure agent-status --from-json data/agent_state/blocked_new_agent.json` | [05](../notebooks/05_agent365_extension.ipynb) | Optional read / licensed manual extension | Verification-required; explicit offline state interpretation | Contract tests, static notebook validation only / PARTIALLY_ALIGNED | Correct fixture paths; publication/consent/Block remain manual, not performed |
| `04_Participant_Lab/No_Code_Security_Lab.md` | Six-pillar ownership and seven-layer evidence | Existing HTML and control/evidence docs | Open local presentation/docs directly | None required | No / no | Explain evidence scopes without claiming product success | HTML tests; no new native signals / ALIGNED_WITH_CAVEAT | No private customer exercises, unpublished appendices or inherited product claims |

No separate participant follow-along notebook was found; seven original
package-backed notebooks were created. Setup and Protect/Prove/Operate deepen
the four paths without introducing another agent implementation.

## Explicit non-alignment

- Cowork `src/fsa` business modules, four model-planned function tools, persistent
  approval queue, unsafe runtime config and bare-Python path: **NOT_IMPLEMENTED**.
  `src/fsa` here is only a thin entry point.
- Extra slide 14b `lifecycle e2e`, conditional-access/access-package/publishing
  simulation: **NOT_IMPLEMENTED**; no fake platform integration added.
- Native registry/activity, Defender and Purview signals: **VERIFICATION_REQUIRED**.
- Redistribution rights and private/presenter-only sources: **BLOCKED** pending
  manual review; no bulk artifact import.
- Cloud/Government feature claims: **VERIFICATION_REQUIRED**, not inferred from
  settings or old source notes.
