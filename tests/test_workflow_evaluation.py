import json
from pathlib import Path
from unittest.mock import patch

import pytest

from foundry_security_accelerator.cli import main
from foundry_security_accelerator.rehearsal import latest_rehearsal, rehearse, trace_tree
from foundry_security_accelerator.workflow_evaluation import (
    evaluate_workflow,
    load_cases,
    replay_case,
    summarize,
)

DATASET = Path("data/evaluation/workflow.jsonl")
THRESHOLDS = Path("data/evaluation/thresholds.toml")


@pytest.mark.evaluation
def test_sixteen_cases_replay_real_workflow_with_measured_denominators(tmp_path: Path) -> None:
    report = evaluate_workflow(DATASET, THRESHOLDS, tmp_path)
    assert report["status"] == "PASS"
    assert report["metrics"] == {
        "task_adherence_rate": 1.0,
        "tool_call_accuracy": 1.0,
        "citation_rate": 1.0,
        "attack_success_rate": 0.0,
        "policy_violations": 0,
        "data_leaks": 0,
    }
    assert report["denominators"]["task_adherence_rate"] == 16
    assert report["denominators"]["attack_success_rate"] == 8
    assert report["denominators"]["citation_rate"] == 8
    assert len(report["results"]) == 16
    assert report == json.loads(Path(report["report"]).read_text())
    for result in report["results"]:
        assert Path(result["audit"]).is_file()
        assert Path(result["traces"]).is_file()
        assert result["evidence_complete"]


@pytest.mark.evaluation
def test_gate_rejects_bad_tool_leak_attack_or_missing_evidence(tmp_path: Path) -> None:
    cases = load_cases(DATASET)
    normal = replay_case(cases[0], tmp_path)
    attack = replay_case(cases[-1], tmp_path)
    for field, value, metric in (
        ("task_adherent", False, "task_adherence_rate"),
        ("tools_correct", False, "tool_call_accuracy"),
        ("citation_valid", False, "citation_rate"),
        ("attack_succeeded", True, "attack_success_rate"),
        ("policy_violations", 1, "policy_violations"),
        ("data_leaks", 1, "data_leaks"),
        ("evidence_complete", False, "evidence_completeness"),
    ):
        report = summarize((normal, attack.model_copy(update={field: value})), THRESHOLDS)
        assert report["status"] == "FAIL"
        assert metric in report["breached"]


def test_no_denial_is_assumed_without_matching_audit_and_trace(tmp_path: Path) -> None:
    case = load_cases(DATASET)[8]
    with (
        patch("foundry_security_accelerator.workflow_evaluation.run", side_effect=PermissionError),
        pytest.raises(FileNotFoundError),
    ):
        replay_case(case, tmp_path)
    result = replay_case(case, tmp_path)
    assert result.status == "BLOCKED" and result.task_adherent
    assert not result.response_observed


@pytest.mark.parametrize("kind", ["empty", "duplicate", "bad-threshold", "nan", "bool"])
def test_invalid_dataset_and_thresholds_fail_explicitly(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "input"
    if kind in ("empty", "duplicate"):
        row = DATASET.read_text().splitlines()[0]
        path.write_text("" if kind == "empty" else row + "\n" + row)
        with pytest.raises(ValueError, match="unique"):
            load_cases(path)
    else:
        content = THRESHOLDS.read_text()
        content = content.replace(
            "task_adherence_rate = 1.0",
            {
                "bad-threshold": "unknown_metric = 1.0",
                "nan": "task_adherence_rate = nan",
                "bool": "task_adherence_rate = true",
            }[kind],
        )
        path.write_text(content)
        cases = load_cases(DATASET)
        results = (replay_case(cases[0], tmp_path), replay_case(cases[-1], tmp_path))
        with pytest.raises(ValueError, match="Threshold"):
            summarize(results, path)


@pytest.mark.evaluation
def test_rehearsal_retains_six_aliases_original_audit_and_trace_trees(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="rehearse first"):
        latest_rehearsal(tmp_path)
    report = rehearse(tmp_path)
    assert report["status"] == "PASS"
    assert report["first_broken_line"] == 2
    assert report["original_audit_verified"]
    scenes = latest_rehearsal(tmp_path).scenes
    assert [scene.case_id for scene in scenes] == ["S1", "S2", "S3", "S4", "S5", "S6"]
    assert [scene.status for scene in scenes] == [
        "AWAITING_APPROVAL",
        "BLOCKED",
        "BLOCKED",
        "AWAITING_APPROVAL",
        "DRY_RUN",
        "AWAITING_APPROVAL",
    ]
    assert "writer" not in trace_tree(tmp_path, "S4")["tree"]
    assert "\n  writer" in trace_tree(tmp_path, "S5")["tree"]
    assert trace_tree(tmp_path, scenes[3].correlation_id[:8])["scene"] == "S4"
    with pytest.raises(ValueError, match="unique"):
        trace_tree(tmp_path, "")
    with pytest.raises(ValueError, match="unique"):
        trace_tree(tmp_path, "S9")
    Path(scenes[3].audit).write_text("{}\n")
    with pytest.raises(ValueError, match="audit"):
        trace_tree(tmp_path, "S4")


def test_trace_rejects_missing_parent_duplicate_and_unrooted_spans(tmp_path: Path) -> None:
    rehearse(tmp_path)
    scene = latest_rehearsal(tmp_path).scenes[0]
    path = Path(scene.traces)
    original = path.read_text().splitlines()
    span = json.loads(original[0])
    for data in (
        [span],
        [span, span],
        [{**span, "parent_id": span["context"]["span_id"]}],
        [],
    ):
        path.write_text("\n".join(json.dumps(item) for item in data))
        with pytest.raises(ValueError, match="ancestry|rooted"):
            trace_tree(tmp_path, "S1")


def test_workflow_and_rehearsal_cli_preserve_modes_and_gate_exit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = ["--state-dir", str(tmp_path)]
    assert main(prefix + ["eval", "--gate"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    with patch(
        "foundry_security_accelerator.workflow_evaluation.evaluate_workflow",
        return_value={"status": "FAIL"},
    ):
        assert main(prefix + ["eval", "--gate"]) == 1
        capsys.readouterr()
    assert main(prefix + ["rehearse"]) == 0
    capsys.readouterr()
    assert main(prefix + ["trace", "list"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 6
    assert main(prefix + ["trace", "show", "S4"]) == 0
    assert json.loads(capsys.readouterr().out)["scene"] == "S4"
    with pytest.raises(ValueError, match="requires"):
        main(prefix + ["trace", "show"])
    with pytest.raises(ValueError, match="local-only"):
        main(["--mode", "azure", "eval", "--gate"])
