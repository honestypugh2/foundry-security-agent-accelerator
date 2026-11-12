"""Evidence-first evaluation without score-polarity assumptions or verdict rewriting."""

import hashlib
import json
import math
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

from azure.identity import DefaultAzureCredential
from pydantic import Field, TypeAdapter

from .config import Settings
from .contracts import (
    Contract,
    EvaluationEvidence,
    EvaluatorVerdict,
    HumanAdjudication,
    Outcome,
    ReleaseGateDecision,
    TraceCompletenessResult,
    VerdictConsistencyResult,
)
from .identity import TenantCredential


def trace_completeness(
    required: tuple[str, ...], observed: tuple[str, ...]
) -> TraceCompletenessResult:
    missing = tuple(stage for stage in required if stage not in observed)
    return TraceCompletenessResult(
        outcome=Outcome.INSUFFICIENT_EVIDENCE if missing else Outcome.PASS, missing=missing
    )


def reconcile(evidence: EvaluationEvidence) -> VerdictConsistencyResult:
    critical = [v for v in evidence.verdicts if v.critical]
    if any(v.outcome == Outcome.FAIL and not v.error for v in critical) or any(
        e.critical and e.executed is True and not e.blocked for e in evidence.executions
    ):
        # Deterministic execution evidence outranks a safe final answer or model verdict.
        outcomes = {v.outcome for v in critical}
        if (
            Outcome.PASS in outcomes
            and Outcome.FAIL in outcomes
            and not any(v.deterministic and v.outcome == Outcome.FAIL for v in critical)
            and not any(
                e.critical and e.executed is True and not e.blocked for e in evidence.executions
            )
        ):
            return VerdictConsistencyResult(
                outcome=Outcome.REVIEW_REQUIRED, reasons=("CONFLICTING_CRITICAL_VERDICTS",)
            )
        return VerdictConsistencyResult(outcome=Outcome.FAIL, reasons=("CRITICAL_FAILURE",))
    if (
        not critical
        or any(v.error or v.taxonomy != evidence.taxonomy for v in critical)
        or any(
            v.outcome in (Outcome.INSUFFICIENT_EVIDENCE, Outcome.NOT_EVALUATED) for v in critical
        )
        or any(
            not any(e.tool == tool and e.executed is not None for e in evidence.executions)
            for tool in evidence.required_tools
        )
        or any(e.attempted and e.executed is None for e in evidence.executions)
        or trace_completeness(evidence.required_stages, evidence.observed_stages).outcome
        != Outcome.PASS
    ):
        return VerdictConsistencyResult(
            outcome=Outcome.INSUFFICIENT_EVIDENCE, reasons=("REQUIRED_EVIDENCE_MISSING_OR_INVALID",)
        )
    if any(v.outcome == Outcome.REVIEW_REQUIRED for v in critical) or any(
        e.critical and e.attempted and e.blocked for e in evidence.executions
    ):
        return VerdictConsistencyResult(
            outcome=Outcome.REVIEW_REQUIRED, reasons=("BLOCKED_ATTEMPT_OR_REVIEW",)
        )
    return VerdictConsistencyResult(outcome=Outcome.PASS, reasons=("REQUIRED_CONTROLS_SATISFIED",))


def release_gate(results: tuple[VerdictConsistencyResult, ...]) -> ReleaseGateDecision:
    if not results:
        return ReleaseGateDecision(
            outcome=Outcome.INSUFFICIENT_EVIDENCE, reasons=("NO_REQUIRED_RESULTS",)
        )
    for outcome in (
        Outcome.FAIL,
        Outcome.INSUFFICIENT_EVIDENCE,
        Outcome.REVIEW_REQUIRED,
        Outcome.NOT_EVALUATED,
    ):
        if any(result.outcome == outcome for result in results):
            return ReleaseGateDecision(
                outcome=outcome, reasons=tuple(r for result in results for r in result.reasons)
            )
    return ReleaseGateDecision(outcome=Outcome.PASS, reasons=("ALL_REQUIRED_GATES_PASS",))


def normalize_record(
    evaluator: str, record: dict[str, object], mapping: dict[str, Outcome]
) -> EvaluatorVerdict:
    raw = json.dumps(record, sort_keys=True)
    value = record.get("verdict")
    outcome = mapping.get(str(value), Outcome.INSUFFICIENT_EVIDENCE)
    error = record.get("error")
    return EvaluatorVerdict(
        evaluator=evaluator,
        outcome=outcome,
        raw_record=raw,
        error=str(error) if error is not None else None,
    )


def adjudicate(
    evidence: EvaluationEvidence, reviewer: str, rationale: str, outcome: Outcome, path: Path
) -> HumanAdjudication:
    record = HumanAdjudication(
        case_id=evidence.case_id,
        reviewer=reviewer,
        rationale=rationale,
        outcome=outcome,
        evidence_digest=hashlib.sha256(evidence.model_dump_json().encode()).hexdigest(),
        recorded_at=datetime.now(UTC),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(record.model_dump_json() + "\n")
    return record


class EvaluationCase(Contract):
    case_id: str = Field(min_length=1)
    classification: str = Field(pattern=r"^synthetic$")
    query: str = Field(min_length=1)
    response: str = Field(min_length=1)
    context: str = Field(min_length=1)


class BatchEvaluator(Protocol):
    def __call__(
        self,
        *,
        data: str,
        evaluators: dict[str, object],
        azure_ai_project: str,
        output_path: str,
        fail_on_evaluator_errors: bool,
        evaluator_config: dict[str, object],
    ) -> object: ...


class EvaluationSDK(Protocol):
    evaluate: BatchEvaluator


class FoundryEvaluator:
    """Service-backed model judging with the stable Microsoft Evaluation SDK."""

    def __init__(self, settings: Settings, batch: BatchEvaluator | None = None) -> None:
        if settings.mode != "azure":
            raise ValueError("Foundry evaluations require Azure mode")
        if settings.cloud != "AzureCloud":
            raise ValueError("Foundry evaluation cloud support VERIFICATION_REQUIRED")
        if not all(
            (
                settings.evaluation_endpoint,
                settings.evaluation_deployment,
                settings.evaluation_api_version,
            )
        ):
            raise ValueError(
                "Explicit evaluation endpoint, judge deployment and API version required"
            )
        self.settings = settings
        self.batch = batch

    def evaluate(
        self, dataset: Path, output_dir: Path, *, authorized: bool = False
    ) -> dict[str, object]:
        if not authorized:
            raise PermissionError("Service evaluation and result upload require --authorize")
        cases = tuple(
            EvaluationCase.model_validate_json(line)
            for line in dataset.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if not cases or len({case.case_id for case in cases}) != len(cases):
            raise ValueError("Nonempty evaluation dataset with unique case IDs required")
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_path = output_dir / "foundry-evaluation.raw.json"
        if raw_path.exists():
            raise FileExistsError("Use a new evidence directory; raw results cannot be overwritten")
        import azure.ai.evaluation as evaluation_sdk
        from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator

        model_config = {
            "azure_endpoint": self.settings.evaluation_endpoint,
            "azure_deployment": self.settings.evaluation_deployment,
            "api_version": self.settings.evaluation_api_version,
        }
        with ExitStack() as stack:
            source = stack.enter_context(DefaultAzureCredential(authority=self.settings.authority))
            credential = TenantCredential(source, self.settings.tenant_id)
            evaluators: dict[str, object] = {
                "relevance": RelevanceEvaluator(
                    model_config=model_config,
                    credential=credential,
                    threshold=self.settings.evaluation_threshold,
                ),
                "groundedness": GroundednessEvaluator(
                    model_config=model_config,
                    credential=credential,
                    threshold=self.settings.evaluation_threshold,
                ),
            }
            batch = self.batch or cast(EvaluationSDK, evaluation_sdk).evaluate
            raw = batch(
                data=str(dataset),
                evaluators=evaluators,
                azure_ai_project=self.settings.project_endpoint,
                output_path=str(raw_path),
                fail_on_evaluator_errors=True,
                evaluator_config={
                    "default": {
                        "column_mapping": {
                            "query": "${data.query}",
                            "response": "${data.response}",
                            "context": "${data.context}",
                        }
                    }
                },
            )
        result = TypeAdapter(dict[str, object]).validate_python(raw)
        # Retain exact SDK-returned records independently of our interpretation.
        if not raw_path.exists():
            with raw_path.open("x", encoding="utf-8") as file:
                json.dump(result, file, default=str)
        rows = TypeAdapter(list[dict[str, object]]).validate_python(result.get("rows", []))
        quality = Outcome.PASS
        returned_ids = [row.get("inputs.case_id") for row in rows]
        if (
            len(rows) != len(cases)
            or any(not isinstance(value, str) for value in returned_ids)
            or {str(value) for value in returned_ids} != {case.case_id for case in cases}
        ):
            quality = Outcome.INSUFFICIENT_EVIDENCE
        for row in rows:
            for evaluator in ("relevance", "groundedness"):
                value = row.get(f"outputs.{evaluator}.{evaluator}")
                if (
                    not isinstance(value, (float, int))
                    or isinstance(value, bool)
                    or not math.isfinite(value)
                    or not 1 <= value <= 5
                ):
                    quality = Outcome.INSUFFICIENT_EVIDENCE
                elif value < self.settings.evaluation_threshold and quality == Outcome.PASS:
                    quality = Outcome.FAIL
        return {
            "kind": "FOUNDRY_SERVICE_EVALUATION",
            "quality_outcome": quality.value,
            "security_release": Outcome.NOT_EVALUATED.value,
            "raw_evidence": str(raw_path),
            "cases": len(cases),
            "project_upload": "REQUESTED_NOT_INDEPENDENTLY_VERIFIED",
        }
