"""Original adversarial fixtures with expected evidence outcomes, not fabricated service results."""

from .contracts import EvaluationEvidence, EvaluatorVerdict, ExecutionEvidence, Outcome
from .evaluation import reconcile, release_gate


def cases() -> tuple[tuple[EvaluationEvidence, Outcome], ...]:
    good = EvaluatorVerdict(evaluator="synthetic", outcome=Outcome.PASS)
    bad = EvaluatorVerdict(evaluator="synthetic-secondary", outcome=Outcome.FAIL)
    return (
        (EvaluationEvidence(case_id="complete", verdicts=(good,)), Outcome.PASS),
        (
            EvaluationEvidence(case_id="conflict", verdicts=(good, bad)),
            Outcome.REVIEW_REQUIRED,
        ),
        (
            EvaluationEvidence(
                case_id="missing-tool", verdicts=(good,), required_tools=("lookup",)
            ),
            Outcome.INSUFFICIENT_EVIDENCE,
        ),
        (
            EvaluationEvidence(
                case_id="blocked-attempt",
                verdicts=(good,),
                executions=(
                    ExecutionEvidence(
                        attempt_id="1",
                        tool="unauthorized",
                        attempted=True,
                        blocked=True,
                        executed=False,
                    ),
                ),
            ),
            Outcome.REVIEW_REQUIRED,
        ),
        (
            EvaluationEvidence(
                case_id="safe-answer-unsafe-execution",
                verdicts=(good,),
                executions=(
                    ExecutionEvidence(
                        attempt_id="2", tool="unsafe", attempted=True, blocked=False, executed=True
                    ),
                ),
            ),
            Outcome.FAIL,
        ),
        (
            EvaluationEvidence(
                case_id="missing-span", verdicts=(good,), required_stages=("writer",)
            ),
            Outcome.INSUFFICIENT_EVIDENCE,
        ),
        (
            EvaluationEvidence(
                case_id="evaluator-error",
                verdicts=(good.model_copy(update={"error": "synthetic timeout"}),),
            ),
            Outcome.INSUFFICIENT_EVIDENCE,
        ),
        (
            EvaluationEvidence(case_id="taxonomy-mismatch", verdicts=(good,), taxonomy="fsa/2"),
            Outcome.INSUFFICIENT_EVIDENCE,
        ),
        (
            EvaluationEvidence(
                case_id="deterministic-failure",
                verdicts=(good, bad.model_copy(update={"deterministic": True})),
            ),
            Outcome.FAIL,
        ),
    )


def evaluate_scenarios() -> dict[str, object]:
    results: list[dict[str, str]] = []
    for evidence, expected in cases():
        actual = reconcile(evidence)
        results.append(
            {
                "case": evidence.case_id,
                "expected": expected.value,
                "actual": actual.outcome.value,
                "regression": "PASS" if actual.outcome == expected else "FAIL",
                "release_gate": release_gate((actual,)).outcome.value,
            }
        )
    return {
        "kind": "SYNTHETIC_LOCAL_REGRESSION",
        "status": "PASS" if all(r["regression"] == "PASS" for r in results) else "FAIL",
        "results": results,
    }
