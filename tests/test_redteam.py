import json
from copy import deepcopy
from pathlib import Path

import pytest

from foundry_security_accelerator.cli import main
from foundry_security_accelerator.redteam import (
    OperatorMetadata,
    RedteamItem,
    load_items,
    reconcile_item,
    reconcile_items,
)

FIXTURE = Path("data/redteam/synthetic_items.json")


@pytest.mark.evaluation
def test_seven_layers_raw_preservation_and_exact_fixture_rates() -> None:
    payload = load_items(FIXTURE)
    before = payload.model_dump_json()
    report = reconcile_items(payload)
    assert payload.model_dump_json() == before
    assert report["strict_failed"] is True
    summary = report["summary"]
    assert summary["raw_asr"] == 5 / 6
    assert summary["confirmed_unsafe_rate"] == 1 / 6
    assert summary["outcome_counts"] == {
        "CONFIRMED_UNSAFE": 1,
        "ATTEMPT_BLOCKED": 2,
        "LIKELY_FALSE_POSITIVE": 1,
        "POLICY_REVIEW": 1,
        "UNKNOWN": 1,
        "CONSISTENT_PASS": 0,
    }
    for source, result in zip(payload.items, report["items"], strict=True):
        assert result["raw"] == source.raw
        assert len(result["layers"]) == 7
        assert result["adjudication"]["status"] == "pending human sign-off"
    assert "HIDDEN_ATTEMPT" in report["items"][2]["flags"]
    assert "SCORE_POLARITY_UNCONFIRMED" in report["items"][5]["flags"]
    report["items"][0]["raw"]["reason"] = "changed copy"
    assert payload.model_dump_json() == before


@pytest.mark.evaluation
def test_strict_cli_preserves_input_bytes_and_rejects_replacing_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["--state-dir", str(tmp_path), "redteam", "reconcile", "--strict"]
    assert main(args) == 1
    assert "STRICT: FAIL (CONFIRMED_UNSAFE=1, UNKNOWN=1)" in capsys.readouterr().out
    assert (tmp_path / "reports/redteam-input.raw").read_bytes() == FIXTURE.read_bytes()
    assert main(args) == 1
    safe = json.loads(FIXTURE.read_text())
    safe["items"] = safe["items"][1:4]
    saved = tmp_path / "safe.json"
    saved.write_text(json.dumps(safe))
    with pytest.raises(FileExistsError):
        main([*args, "--input", str(saved)])
    assert (
        main(
            [
                "--state-dir",
                str(tmp_path / "safe"),
                "redteam",
                "reconcile",
                "--strict",
                "--json",
                "--input",
                str(saved),
            ]
        )
        == 0
    )
    capsys.readouterr()


@pytest.mark.evaluation
@pytest.mark.parametrize(
    "missing", ["tool_invocations", "authorization", "executions", "downstream", "trace_complete"]
)
def test_missing_action_evidence_never_passes(missing: str) -> None:
    row = json.loads(FIXTURE.read_text())["items"][3]
    row["raw"] = {"passed": True}
    del row["evidence"][missing]
    result = reconcile_item(RedteamItem.model_validate(row), OperatorMetadata())
    assert result["outcome"] == "UNKNOWN"
    assert "MISSING_ACTION_EVIDENCE" in result["flags"]


@pytest.mark.evaluation
def test_unsafe_execution_overrides_safe_verdict_and_missing_trace() -> None:
    row = json.loads(FIXTURE.read_text())["items"][0]
    row["raw"] = {"passed": True}
    row["evidence"]["trace_complete"] = False
    result = reconcile_item(RedteamItem.model_validate(row), OperatorMetadata())
    assert result["outcome"] == "CONFIRMED_UNSAFE"
    assert "HIDDEN_ATTEMPT" in result["flags"]


@pytest.mark.evaluation
def test_pass_requires_complete_no_attempt_and_score_polarity_is_not_guessed() -> None:
    row = json.loads(FIXTURE.read_text())["items"][3]
    row["raw"] = {"passed": True}
    assert (
        reconcile_item(RedteamItem.model_validate(row), OperatorMetadata())["outcome"]
        == "CONSISTENT_PASS"
    )
    row["raw"] = {
        "score": 0.9,
        "threshold": 0.5,
        "evaluator": "synthetic",
        "evaluator_version": "1",
    }
    item = RedteamItem.model_validate(row)
    assert reconcile_item(item, OperatorMetadata())["outcome"] == "UNKNOWN"
    metadata = OperatorMetadata(confirmed_score_polarity={"synthetic@1": "higher_is_safer"})
    assert reconcile_item(item, metadata)["outcome"] == "CONSISTENT_PASS"
    reversed_polarity = OperatorMetadata(confirmed_score_polarity={"synthetic@1": "lower_is_safer"})
    assert reconcile_item(item, reversed_polarity)["outcome"] == "LIKELY_FALSE_POSITIVE"
    row["raw"] = {"passed": True, "attack_success": True}
    assert reconcile_item(RedteamItem.model_validate(row), metadata)["outcome"] == "UNKNOWN"


@pytest.mark.evaluation
def test_unmatched_execution_cannot_prove_attempt_blocked() -> None:
    row = json.loads(FIXTURE.read_text())["items"][1]
    row["evidence"]["executions"][0]["tool"] = "different"
    assert (
        reconcile_item(RedteamItem.model_validate(row), OperatorMetadata())["outcome"] == "UNKNOWN"
    )


@pytest.mark.evaluation
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization", {}),
        ("downstream", {}),
        ("executions", [{"tool": "synthetic_write", "risky": True}]),
    ],
)
def test_empty_or_unknown_action_details_are_not_complete(field: str, value: object) -> None:
    row = json.loads(FIXTURE.read_text())["items"][1]
    row["evidence"][field] = value
    result = reconcile_item(RedteamItem.model_validate(row), OperatorMetadata())
    assert result["outcome"] == "UNKNOWN"


def test_nonfinite_json_export_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nonfinite.json"
    path.write_text('[{"id":"synthetic","raw":{"score":NaN}}]')
    with pytest.raises(ValueError, match="Nonfinite"):
        load_items(path)


@pytest.mark.parametrize("kind", ["json", "jsonl"])
def test_list_and_jsonl_exports_and_duplicate_ids(tmp_path: Path, kind: str) -> None:
    rows = json.loads(FIXTURE.read_text())["items"]
    path = tmp_path / f"export.{kind}"
    path.write_text(
        json.dumps(rows) if kind == "json" else "\n".join(json.dumps(row) for row in rows)
    )
    assert len(load_items(path).items) == 6
    if kind == "json":
        path.write_text(json.dumps([rows[0], deepcopy(rows[0])]))
        with pytest.raises(ValueError, match="unique"):
            load_items(path)
        path.write_text("[]")
        with pytest.raises(ValueError):
            load_items(path)


def test_evidence_pack_does_not_promote_saved_files_to_platform_observations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--state-dir", str(tmp_path), "evidence"]) == 0
    pack = tmp_path / "reports/evidence-pack.md"
    assert "Agent 365 registry / governance state | NOT OBSERVED IN THIS MODE" in pack.read_text()
    assert main(["--mode", "azure", "--state-dir", str(tmp_path), "evidence"]) == 0
    assert "Agent 365 registry / governance state | NOT CHECKED HERE" in pack.read_text()
    assert main(["--state-dir", str(tmp_path), "redteam", "reconcile", "--json"]) == 0
    assert main(["--state-dir", str(tmp_path), "evidence"]) == 0
    assert "Red-team reconciliation | SAVED REPORT PRESENT (NOT VERIFIED)" in pack.read_text()
    capsys.readouterr()
