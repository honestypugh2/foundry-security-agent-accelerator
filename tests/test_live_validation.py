import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from azure.core.exceptions import HttpResponseError

from foundry_security_accelerator import live_validation as live
from foundry_security_accelerator.config import Settings
from foundry_security_accelerator.contracts import UserRequest
from foundry_security_accelerator.retrieval import DOCUMENTS, retrieve
from foundry_security_accelerator.security import LocalInspector
from foundry_security_accelerator.workflow import run


@pytest.fixture
def settings() -> Settings:
    return Settings(
        mode="azure",
        tenant_id="synthetic",
        subscription_id="synthetic",
        project_endpoint="https://synthetic.services.ai.azure.com/api/projects/synthetic",
        model_deployment="synthetic",
        agent_version="1",
        search_endpoint="https://synthetic.search.windows.net",
        search_index="synthetic",
        content_safety_endpoint="https://synthetic.cognitiveservices.azure.com",
        export_monitor=True,
        monitor_connection_string=(
            "InstrumentationKey=synthetic;"
            "IngestionEndpoint=https://synthetic.in.applicationinsights.azure.com/"
        ),
        logs_workspace_id="synthetic",
        _env_file=None,
    )


def test_authorization_and_account_mismatch_stop_before_services(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(PermissionError):
        live.validate_live(settings, tmp_path / "unauthorized")
    with pytest.raises(PermissionError):
        live.check_live_boundaries(settings)
    monkeypatch.setattr(live, "whoami", lambda settings: {"status": "FAIL"})
    search = MagicMock()
    monkeypatch.setattr(live, "AzureSearchRetriever", search)
    report = live.validate_live(settings, tmp_path / "mismatch", authorized=True)
    assert report["status"] == "FAIL"
    search.assert_not_called()


def test_boundary_checks_require_real_evidence(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(live, "whoami", lambda settings: {"status": "PASS"})
    search = MagicMock()
    search.search.return_value = ()
    monkeypatch.setattr(live, "AzureSearchRetriever", lambda settings: search)
    with pytest.raises(RuntimeError, match="No synthetic"):
        live.check_live_boundaries(settings, authorized=True)


@pytest.mark.parametrize("ingested", [True, False, None])
def test_full_checks_call_budget_denials_and_ingestion(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ingested: bool | None
) -> None:
    if ingested is None:
        settings = settings.model_copy(update={"export_monitor": False})
    monkeypatch.setattr(live, "check_live_boundaries", MagicMock())
    monkeypatch.setattr(live, "fetch_agent_status", MagicMock())
    adapter = MagicMock()
    adapter.invoke.return_value = "Independent approval required. [equipment-001]"
    monkeypatch.setattr(live, "FoundryAdapter", lambda settings: adapter)

    class SyntheticRetriever:
        def search(self, request: UserRequest):
            return retrieve(request, DOCUMENTS)

    def fake_services(*args, **kwargs):
        kwargs["settings"] = settings.model_copy(update={"export_monitor": False})
        kwargs["retriever"] = SyntheticRetriever()
        kwargs["inspector"] = LocalInspector()
        result = run(*args, **kwargs)
        result["telemetry_export"] = "SENT_NOT_INGESTION_PROOF"
        return result

    monkeypatch.setattr(live, "run", fake_services)
    query = MagicMock(
        return_value={"outcome": "PASS", "rows": [{}]}
        if ingested
        else {"outcome": "INSUFFICIENT_EVIDENCE", "rows": []}
    )
    monkeypatch.setattr(live, "query_azure_traces", query)
    monkeypatch.setattr(live, "sleep", MagicMock())
    report = live.validate_live(settings, tmp_path / "full", authorized=True)
    assert report["status"] == ("PARTIAL" if ingested is None else ("PASS" if ingested else "FAIL"))
    assert adapter.invoke.call_count == 2
    assert query.call_count == (0 if ingested is None else (1 if ingested else 3))
    assert not list(tmp_path.rglob("receipts.sqlite3"))


def test_failures_do_not_leak_sdk_messages(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        live, "check_live_boundaries", MagicMock(side_effect=RuntimeError("private-service-value"))
    )
    report = live.validate_live(settings, tmp_path / "failed", authorized=True)
    assert report["status"] == "FAIL"
    assert "private-service-value" not in json.dumps(report)
    assert report["checks"][-1]["error_type"] == "RuntimeError"


@pytest.mark.parametrize("exists", [False, True])
def test_iq_discovery_never_queries_or_creates_sources(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, exists: bool
) -> None:
    monkeypatch.setattr(live, "whoami", lambda settings: {"status": "PASS"})
    monkeypatch.setattr(live, "DefaultAzureCredential", MagicMock())
    client = MagicMock()
    client.list_knowledge_bases.return_value = [object()] if exists else []
    factory = MagicMock()
    factory.return_value.__enter__.return_value = client
    monkeypatch.setattr(live, "SearchIndexClient", factory)
    report = live.inspect_foundry_iq(settings, authorized=True)
    assert report["status"] == ("SCOPE_REVIEW_REQUIRED" if exists else "NOT_CONFIGURED")
    client.list_knowledge_bases.assert_called_once_with(page_size=1)
    assert len(client.mock_calls) == 1
    client.list_knowledge_bases.side_effect = HttpResponseError("private-service-value")
    report = live.inspect_foundry_iq(settings, authorized=True)
    assert report["status"] == "BLOCKED"
    assert "private-service-value" not in json.dumps(report)
