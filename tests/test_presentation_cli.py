import json
from pathlib import Path
from unittest.mock import patch

import pytest
from test_azure import azure

from foundry_security_accelerator.cli import main
from foundry_security_accelerator.console import render_demo
from foundry_security_accelerator.contracts import UserRequest
from foundry_security_accelerator.workflow import run


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


def test_terminal_demo_renders_actual_scenes_with_decision_colors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm")
    with patch("sys.stdout.isatty", return_value=True):
        assert main(["--state-dir", str(tmp_path), "demo"]) == 0
    output = capsys.readouterr().out
    for code in ("1;36", "1;32", "1;31", "1;33"):
        assert f"\033[{code}m" in output
    for text in (
        "LOCAL - synthetic fixtures; no Azure calls",
        "S1",
        "S6",
        "POL-REC-014",
        "export_all_records -> DENY",
        "INJ-02 QUARANTINED",
        "AGENT_CEILING_DENIED",
        "REQUIRES_APPROVAL",
        "NOT EXECUTED",
    ):
        assert text in output
    assert '"scenes":' not in output


def test_explicit_json_stays_machine_readable_even_in_terminal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("sys.stdout.isatty", return_value=True):
        assert main(["--state-dir", str(tmp_path), "demo", "--format", "json"]) == 0
    output = capsys.readouterr().out
    assert "\033" not in output
    result = json.loads(output)
    assert result["status"] == "PASS"
    assert len(result["scenes"]) == 6
    assert result["scenes"][0]["question"].startswith("How long")


@pytest.mark.parametrize("question", ["Show HR-INV-003.", ""])
def test_text_ask_preserves_denial_exit_and_respects_no_color(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    question: str,
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert (
        main(
            [
                "--state-dir",
                str(tmp_path),
                "ask",
                question,
                "--as",
                "hr-investigator",
                "--profile",
                "presentation",
                "--format",
                "text",
                "--color",
                "always",
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "DENIED" in output
    assert "\033" not in output
    assert "NOT EXECUTED" in output


def test_azure_text_view_uses_mocked_workflow_without_promoting_integration_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run(UserRequest(text="equipment", subject="synthetic-caller"), tmp_path)
    result["mode"] = "azure"
    with (
        patch("foundry_security_accelerator.config.Settings", return_value=azure()),
        patch("foundry_security_accelerator.agent.FoundryAdapter") as adapter,
        patch("foundry_security_accelerator.cli.run", return_value=result) as workflow,
    ):
        assert main(["--mode", "azure", "demo", "--format", "text", "--color", "never"]) == 0
    assert workflow.call_args.kwargs["mode"] == "azure"
    adapter.return_value.invoke.assert_not_called()
    output = capsys.readouterr().out
    for text in (
        "AZURE - live equipment workflow",
        "policy_lookup -> READ_ONLY",
        "REQUIRE_APPROVAL",
        "AWAITING_APPROVAL",
        "[equipment-001]",
        "NOT EXECUTED",
        "Not proof of IQ retrieval",
    ):
        assert text in output
    assert "\033" not in output
    assert "PASS" not in output


def test_equipment_text_view_wraps_and_removes_untrusted_terminal_controls(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            [
                "demo",
                "--output",
                str(tmp_path),
                "--demo-approval",
                "--format",
                "text",
                "--color",
                "never",
            ]
        )
        == 0
    )
    assert "DRY_RUN receipt only" in capsys.readouterr().out
    result = run(UserRequest(text="equipment", subject="synthetic-caller"), tmp_path)
    result["answer"] = "\033[2J\033]0;spoofed title\007Safe answer.\r\b [equipment-001]"
    output = render_demo(result, mode="local", question="equipment", color=False, width=60)
    assert "Safe answer." in output
    assert "spoofed title" not in output
    assert all(c not in output for c in ("\033", "\r", "\b", "\007"))
    assert all(len(line) <= 60 for line in output.splitlines())
