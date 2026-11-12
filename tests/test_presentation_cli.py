import json
from pathlib import Path
from unittest.mock import patch

import pytest

from foundry_security_accelerator.cli import main


def test_presenter_demo_trace_and_implicit_audit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = ["--state-dir", str(tmp_path)]
    assert main(prefix + ["demo"]) == 0
    demo = json.loads(capsys.readouterr().out)
    assert demo["status"] == "PASS"
    assert main(prefix + ["audit", "verify"]) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "PASS"
    assert main(prefix + ["trace", "show", "S4"]) == 0
    trace = json.loads(capsys.readouterr().out)
    assert "export_all_records" in json.dumps(trace)
    assert main(prefix + ["lifecycle", "e2e"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"


def test_unsafe_config_is_local_only_and_gate_rejects_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = [
        "eval",
        "--config",
        "agents/policy-assistant.unsafe.toml",
        "--gate",
    ]
    assert main(["--state-dir", str(tmp_path), *args]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "FAIL"
    assert report["metrics"]["attack_success_rate"] > 0
    with pytest.raises(ValueError, match="local-only"):
        main(["--mode", "azure", *args])
    with pytest.raises(PermissionError, match="local-only"):
        main(["--mode", "azure", "lifecycle", "e2e"])


def test_legacy_create_agent_is_noop_without_authorization(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch("foundry_security_accelerator.agent.FoundryAdapter") as adapter:
        assert main(["azure", "create-agent"]) == 0
    adapter.assert_not_called()
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_EXECUTED"


def test_exact_presenter_role_labels_retrieve_retention_and_deny_hr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = ["--state-dir", str(tmp_path)]
    assert (
        main(
            prefix
            + [
                "ask",
                "How long must we retain email of elected officials?",
                "--as",
                "analyst",
            ]
        )
        == 0
    )
    retention = json.loads(capsys.readouterr().out)
    assert retention["status"] != "DENIED"
    assert "POL-REC-014" in json.dumps(retention)
    assert main(prefix + ["ask", "Show HR-INV-003", "--as", "hr-investigator"]) == 1
    denied = json.loads(capsys.readouterr().out)
    assert denied["status"] == "DENIED"
    assert denied["effective_classifications"] == ["Internal", "Public"]


def test_legacy_saved_agent_state_is_explicitly_offline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            [
                "azure",
                "agent-status",
                "--from-json",
                "src/fsa/data/agent_state/blocked_new_agent.json",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "offline - not a live observation" in output
    assert "SIMULATED" in output
