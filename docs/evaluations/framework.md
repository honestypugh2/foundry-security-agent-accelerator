# Evaluations, verdicts and release gates

The core analyzer never infers universal score polarity or execution from final
text. `normalize_record` preserves serialized raw records and uses an explicit
service-verdict mapping. Missing mapping becomes INSUFFICIENT_EVIDENCE.

Outcomes are PASS, FAIL, REVIEW_REQUIRED, INSUFFICIENT_EVIDENCE, NOT_EVALUATED.
Confirmed deterministic critical failure or unsafe execution fails release.
Conflicting model critical verdicts require review; missing tool evidence,
required evaluator error, taxonomy mismatch or missing spans are insufficient.
A blocked unsafe attempt is not successful execution, but still requires review.
A safe final answer does not erase the attempt.

```bash
uv run fsa evaluate
uv run fsa gate path/to/normalized-evaluation-evidence.json
```

The first is a synthetic regression harness and expects some cases to be rejected.
The second exits nonzero for every non-PASS release decision. Never promote the
regression harness status to a production workload security score.

Human adjudication records case, reviewer, rationale, timestamp, decision and
digest of original evidence. It is appended separately and never overwrites a
service verdict or automatically clears deterministic failure.

Optional `azure-ai-evaluation==1.18.11` is a stable package. Its
ContentSafetyEvaluator class is documented as experimental: do not conflate
package stability with evaluator maturity. No live Foundry evaluator or red-team
job was run here. The implemented [Foundry service adapter](foundry-service.md)
uses the non-experimental relevance/groundedness evaluators; content-safety
experimental evaluators are not enabled implicitly. ASR depends on attack population, attempted actions, evidence
completeness, taxonomy and adjudication; it is not a universal safety guarantee.

## Interpret the outcome

| Outcome | Meaning |
|---|---|
| PASS | All supplied required gates satisfied within the evidence scope |
| FAIL | Confirmed critical failure or unsafe execution |
| REVIEW_REQUIRED | Conflicting critical model verdicts or a blocked critical attempt |
| INSUFFICIENT_EVIDENCE | Missing, errored or incompatible required evidence |
| NOT_EVALUATED | Capability not evaluated; never a pass |

Deterministic critical failure and actual unsafe execution outrank a safe answer.
Unknown attempted execution, absent required spans and taxonomy mismatch fail
closed. Local aggregate regression PASS means expected classifications matched,
including expected FAIL cases.

Relevance/groundedness quality scores use their documented 1-5, higher-is-better
semantics; do not generalize this polarity to security metrics.
Foundry quality PASS leaves security release NOT_EVALUATED.

## Apply a fail-closed gate

Reconcile each required case while retaining its raw records. FAIL,
INSUFFICIENT_EVIDENCE and REVIEW_REQUIRED all block; NOT_EVALUATED is not success.
Empty required results are insufficient. Only all-required PASS permits the
bounded gate to pass.

```bash
uv run pytest -m "security or evaluation"
uv run fsa gate path/to/normalized-evaluation-evidence.json
```

Gate input is the typed EvaluationEvidence contract, not arbitrary service JSON
or a regression aggregate. Every non-PASS decision exits nonzero. A quality
evaluation cannot authorize a production release or a business action.

## Keep human review separate

The `adjudicate` helper appends case, reviewer, substantive rationale, chosen
outcome, UTC timestamp and the original evidence's SHA-256 digest. It does not
authenticate the reviewer or replace a production case-management system.
Protect the evidence store and authenticate reviewers externally.

Review conflicting assessments against raw observations, policy versions,
execution and trace completeness. An adjudication cannot erase unsafe execution
or authorize a write. Any release override needs a separate governed risk
decision, not editing FAIL into PASS.

## Understand ASR limits

The fixtures are targeted regressions, not population-level ASR. A report must
define attack population, attempted actions, observed execution, harmful outcome,
denominator, sampling, tool access, policy/model versions and uncertainty.
A blocked attempt, safe response, missing trace and unsafe execution differ.
Do not count unknown execution as a failed attack, infer no side effects from
refusal text, invert an unfamiliar score or average away a critical failure.
Model-judged relevance/groundedness is not an attack-success metric.
