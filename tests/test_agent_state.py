import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from azure.ai.projects.models import AgentDetails
from azure.core.exceptions import HttpResponseError
from test_azure import azure

from foundry_security_accelerator.agent_state import (
    fetch_agent_status,
    interpret_agent_state,
    normalize_agent_state,
)
from foundry_security_accelerator.azure_ops import main
from foundry_security_accelerator.config import Settings


@pytest.mark.parametrize(
    ("fixture", "diagnosis"),
    [
        ("enabled_agent", "both permit operation"),
        ("blocked_new_agent", "Disabled by Entra admin state on the agent identity"),
        ("legacy_exception", "LEGACY EXCEPTION"),
    ],
)
def test_agent_state_fixture_cli_is_explicitly_offline(
    fixture: str, diagnosis: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("foundry_security_accelerator.agent_state.fetch_agent_status") as live:
        assert main(["agent-status", "--from-json", f"data/agent_state/{fixture}.json"]) == 0
    live.assert_not_called()
    text = capsys.readouterr().out
    assert "offline - not a live observation" in text
    assert "SIMULATED / SAVED EVIDENCE" in text
    assert diagnosis in text
    assert "10 minutes" in text


@pytest.mark.parametrize(
    ("raw", "diagnosis"),
    [
        ({}, "not recognised"),
        ({"state": "unknown-new-state"}, "not recognised"),
        ({"state": "enabled"}, "not confirmed fully enabled"),
        ({"state": "disabled"}, "check the Foundry portal"),
        (
            {"state": "disabled", "state_source": "agent_blueprint"},
            "agent blueprint",
        ),
        (
            {"state": "disabled", "configuration_state": "disabled"},
            "developer configuration",
        ),
        (
            {
                "state": "disabled",
                "configuration_state": "disabled",
                "instance_identity": {"status": "disabled"},
            },
            "An Entra block is also reported",
        ),
        (
            {"state": "enabled", "blueprint": {"status": "disabled"}},
            "LEGACY EXCEPTION",
        ),
    ],
)
def test_agent_state_missing_disabled_and_legacy_rules(
    raw: dict[str, object], diagnosis: str
) -> None:
    lines = interpret_agent_state(normalize_agent_state(raw))
    assert len(lines) == 3
    assert diagnosis in lines[1]


def test_agent_state_sdk_objects_and_as_dict_match() -> None:
    raw = json.loads(Path("data/agent_state/enabled_agent.json").read_text())

    class SavedSDKObject:
        def as_dict(self) -> dict[str, object]:
            return raw

    attributes = SimpleNamespace(
        name=raw["name"],
        state="enabled",
        configuration_state="enabled",
        instance_identity=SimpleNamespace(status="active"),
        blueprint=SimpleNamespace(status="active"),
        versions=SimpleNamespace(latest=SimpleNamespace(version="1")),
    )
    assert normalize_agent_state(SavedSDKObject()) == normalize_agent_state(raw)
    assert normalize_agent_state(attributes) == normalize_agent_state(raw)


def test_agent_status_uses_only_installed_sdk_get() -> None:
    raw = json.loads(Path("data/agent_state/blocked_new_agent.json").read_text())
    with (
        patch("azure.identity.DefaultAzureCredential"),
        patch("azure.ai.projects.AIProjectClient") as factory,
    ):
        project = factory.return_value.__enter__.return_value
        project.agents.get.return_value = AgentDetails(raw)
        result = fetch_agent_status(azure())
    project.agents.get.assert_called_once_with(agent_name=azure().agent_name)
    assert [call[0] for call in project.mock_calls] == ["agents.get"]
    assert result["state"] == "disabled"
    with pytest.raises(ValueError):
        fetch_agent_status(Settings())


@pytest.mark.parametrize(
    "error", [ImportError(), HttpResponseError(), ValueError(), TimeoutError()]
)
def test_status_read_errors_return_two_without_secret_details(
    error: Exception, capsys: pytest.CaptureFixture[str]
) -> None:
    with (
        patch("foundry_security_accelerator.azure_ops.Settings", return_value=azure()),
        patch("foundry_security_accelerator.agent_state.fetch_agent_status", side_effect=error),
    ):
        assert main(["agent-status"]) == 2
    assert "unavailable" in capsys.readouterr().out


def test_status_invalid_json_is_not_enabled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file = tmp_path / "invalid.json"
    file.write_text("[]")
    assert main(["agent-status", "--from-json", str(file)]) == 2
    assert "Enabled:" not in capsys.readouterr().out
