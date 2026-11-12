# Evidence-first evaluations

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
