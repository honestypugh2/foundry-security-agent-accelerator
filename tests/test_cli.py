import json
from pathlib import Path
from unittest.mock import patch

import pytest
from test_azure import azure

from foundry_security_accelerator.cli import main
from foundry_security_accelerator.contracts import (
    EvaluationEvidence,
    EvaluatorVerdict,
    Outcome,
    UserRequest,
)
from foundry_security_accelerator.workflow import run


def test_demo_evaluate_and_audit_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["demo", "--output", str(tmp_path), "--demo-approval"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert main(["audit-verify", result["audit"], "--expected-head", result["audit_head"]]) == 0
    capsys.readouterr()
    assert main(["trace-check", "--trace", result["traces"]]) == 0
    capsys.readouterr()
    assert main(["evaluate"]) == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "SYNTHETIC_LOCAL_REGRESSION"


@pytest.mark.evaluation
@pytest.mark.parametrize("outcome", list(Outcome))
def test_release_gate_exit_is_fail_closed(
    tmp_path: Path, outcome: Outcome, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = EvaluationEvidence(
        case_id="synthetic", verdicts=(EvaluatorVerdict(evaluator="test", outcome=outcome),)
    )
    path = tmp_path / "evidence.json"
    path.write_text(evidence.model_dump_json())
    assert main(["gate", str(path)]) == (0 if outcome == Outcome.PASS else 1)
    assert json.loads(capsys.readouterr().out)["outcome"] == (
        "INSUFFICIENT_EVIDENCE" if outcome == Outcome.NOT_EVALUATED else outcome.value
    )


def test_trace_command_cannot_pass_incomplete_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run(UserRequest(text="equipment", subject="caller"), tmp_path)
    assert main(["trace-check", "--trace", result["traces"]]) == 1
    assert json.loads(capsys.readouterr().out)["outcome"] == "INSUFFICIENT_EVIDENCE"


def test_audit_cli_reports_first_tampered_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run(UserRequest(text="equipment", subject="caller"), tmp_path)
    path = Path(result["audit"])
    records = path.read_text().splitlines()
    records[1] = records[1].replace("input-security", "input-securitx", 1)
    path.write_text("\n".join(records) + "\n")
    assert main(["audit-verify", str(path)]) == 1
    decision = json.loads(capsys.readouterr().out)
    assert decision == {"outcome": "FAIL", "first_broken_line": 2}


@pytest.mark.evaluation
@pytest.mark.parametrize("quality", ["PASS", "FAIL", "INSUFFICIENT_EVIDENCE"])
def test_azure_evaluation_cli_preserves_authorization_and_quality_exit(
    tmp_path: Path, quality: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with (
        patch("foundry_security_accelerator.config.Settings", return_value=azure()),
        patch("foundry_security_accelerator.evaluation.FoundryEvaluator") as evaluator,
    ):
        evaluator.return_value.evaluate.return_value = {
            "quality_outcome": quality,
            "security_release": "NOT_EVALUATED",
        }
        assert main(
            [
                "evaluate",
                "--mode",
                "azure",
                "--data",
                "data/evaluation/smoke.jsonl",
                "--output",
                str(tmp_path),
                "--authorize",
            ]
        ) == (0 if quality == "PASS" else 1)
        assert evaluator.return_value.evaluate.call_args.kwargs["authorized"] is True
        assert json.loads(capsys.readouterr().out)["security_release"] == "NOT_EVALUATED"
        with pytest.raises(ValueError, match="require --data"):
            main(["evaluate", "--mode", "azure"])


def test_observation_cli_cannot_promote_missing_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch("foundry_security_accelerator.config.Settings", return_value=azure()),
        patch(
            "foundry_security_accelerator.observability.query_azure_traces",
            return_value={"outcome": "INSUFFICIENT_EVIDENCE", "rows": []},
        ),
    ):
        assert (
            main(
                [
                    "observe",
                    "--correlation-id",
                    str(UserRequest(text="hi", subject="s").correlation_id),
                ]
            )
            == 1
        )
        assert json.loads(capsys.readouterr().out)["outcome"] == "INSUFFICIENT_EVIDENCE"
