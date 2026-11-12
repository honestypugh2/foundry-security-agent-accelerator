import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from azure.core.credentials import AccessToken
from azure.monitor.query import LogsQueryResult, LogsTable
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from test_azure import azure

from foundry_security_accelerator.agent365 import main as agent365_main
from foundry_security_accelerator.agent365 import resource_status
from foundry_security_accelerator.azure_ops import infrastructure
from foundry_security_accelerator.azure_ops import main as azure_main
from foundry_security_accelerator.config import Settings
from foundry_security_accelerator.contracts import UserRequest
from foundry_security_accelerator.evaluation import FoundryEvaluator
from foundry_security_accelerator.identity import TenantCredential
from foundry_security_accelerator.observability import (
    DeliveryExporter,
    RunTracing,
    query_azure_traces,
)
from foundry_security_accelerator.retrieval import LocalRetriever
from foundry_security_accelerator.security import LocalInspector
from foundry_security_accelerator.workflow import run


def judge_settings(**overrides: object) -> Settings:
    return azure(
        evaluation_endpoint="https://synthetic.openai.azure.com",
        evaluation_deployment="synthetic-judge",
        evaluation_api_version="2024-10-21",
        **overrides,
    )


@pytest.mark.evaluation
def test_real_sdk_evaluation_contract_and_quality_not_security(tmp_path: Path) -> None:
    batch = MagicMock(
        return_value={
            "rows": [
                {
                    "inputs.case_id": "synthetic-equipment-policy",
                    "outputs.relevance.relevance": 4,
                    "outputs.groundedness.groundedness": 5,
                }
            ]
        }
    )
    service = FoundryEvaluator(judge_settings(), batch)
    dataset = Path("data/evaluation/smoke.jsonl")
    with pytest.raises(PermissionError):
        service.evaluate(dataset, tmp_path)
    with (
        patch("azure.ai.evaluation.RelevanceEvaluator") as relevance,
        patch("azure.ai.evaluation.GroundednessEvaluator") as grounded,
    ):
        result = service.evaluate(dataset, tmp_path, authorized=True)
    assert result["quality_outcome"] == "PASS"
    assert result["security_release"] == "NOT_EVALUATED"
    assert json.loads(Path(str(result["raw_evidence"])).read_text()) == batch.return_value
    assert batch.call_args.kwargs["fail_on_evaluator_errors"] is True
    assert batch.call_args.kwargs["azure_ai_project"] == judge_settings().project_endpoint
    assert set(batch.call_args.kwargs["evaluators"]) == {"relevance", "groundedness"}
    assert relevance.call_args.kwargs["threshold"] == 3
    grounded.assert_called_once()
    with pytest.raises(FileExistsError):
        service.evaluate(dataset, tmp_path, authorized=True)


@pytest.mark.evaluation
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"rows": []}, "INSUFFICIENT_EVIDENCE"),
        ({"rows": [{"outputs.relevance.relevance": 5}]}, "INSUFFICIENT_EVIDENCE"),
        (
            {
                "rows": [
                    {
                        "outputs.relevance.relevance": 2,
                        "outputs.groundedness.groundedness": 4,
                    }
                ]
            },
            "FAIL",
        ),
        (
            {
                "rows": [
                    {
                        "outputs.relevance.relevance": True,
                        "outputs.groundedness.groundedness": 5,
                    }
                ]
            },
            "INSUFFICIENT_EVIDENCE",
        ),
    ],
)
def test_foundry_judge_missing_low_and_invalid_values_fail_closed(
    tmp_path: Path,
    raw: dict[str, object],
    expected: str,
) -> None:
    for row in raw.get("rows", []):
        row["inputs.case_id"] = "synthetic-equipment-policy"
    with (
        patch("azure.ai.evaluation.RelevanceEvaluator"),
        patch("azure.ai.evaluation.GroundednessEvaluator"),
    ):
        result = FoundryEvaluator(judge_settings(), MagicMock(return_value=raw)).evaluate(
            Path("data/evaluation/smoke.jsonl"),
            tmp_path,
            authorized=True,
        )
    assert result["quality_outcome"] == expected


def test_foundry_settings_dataset_and_errors_do_not_downgrade(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        FoundryEvaluator(Settings())
    with pytest.raises(ValueError):
        FoundryEvaluator(azure())
    gov = azure(
        cloud="AzureUSGovernment",
        project_endpoint="https://synthetic.services.ai.azure.us/api/projects/synthetic",
        search_endpoint="https://synthetic.search.azure.us",
        content_safety_endpoint="",
    )
    with pytest.raises(ValueError, match="VERIFICATION_REQUIRED"):
        FoundryEvaluator(gov)
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    with pytest.raises(ValueError):
        FoundryEvaluator(judge_settings()).evaluate(empty, tmp_path, authorized=True)
    with (
        patch("azure.ai.evaluation.RelevanceEvaluator"),
        patch("azure.ai.evaluation.GroundednessEvaluator"),
        pytest.raises(TimeoutError),
    ):
        FoundryEvaluator(judge_settings(), MagicMock(side_effect=TimeoutError())).evaluate(
            Path("data/evaluation/smoke.jsonl"),
            tmp_path,
            authorized=True,
        )


@pytest.mark.evaluation
@pytest.mark.parametrize(
    "returned_ids", [("case-a", "case-a"), ("case-a", "wrong"), (None, "case-b")]
)
def test_foundry_rows_must_match_unique_dataset_cases(
    tmp_path: Path, returned_ids: tuple[str | None, str | None]
) -> None:
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        "\n".join(
            json.dumps(
                {
                    "case_id": case_id,
                    "classification": "synthetic",
                    "query": "equipment policy",
                    "response": "approval required",
                    "context": "Equipment requires approval.",
                }
            )
            for case_id in ("case-a", "case-b")
        )
    )
    raw = {
        "rows": [
            {
                "inputs.case_id": case_id,
                "outputs.relevance.relevance": 5,
                "outputs.groundedness.groundedness": 5,
            }
            for case_id in returned_ids
        ]
    }
    with (
        patch("azure.ai.evaluation.RelevanceEvaluator"),
        patch("azure.ai.evaluation.GroundednessEvaluator"),
    ):
        result = FoundryEvaluator(judge_settings(), MagicMock(return_value=raw)).evaluate(
            dataset, tmp_path / "output", authorized=True
        )
    assert result["quality_outcome"] == "INSUFFICIENT_EVIDENCE"
    assert json.loads(Path(str(result["raw_evidence"])).read_text()) == raw


def test_telemetry_json_azure_and_otlp_routing(tmp_path: Path) -> None:
    local = RunTracing(tmp_path / "local.jsonl")
    with local.tracer.start_as_current_span("local"):
        pass
    local.close()
    assert local.export_status == "LOCAL_ONLY"
    exporter = InMemorySpanExporter()
    connection = "InstrumentationKey=synthetic;IngestionEndpoint=https://synthetic.in.applicationinsights.azure.com/"
    settings = azure(export_monitor=True, monitor_connection_string=connection)
    with patch(
        "azure.monitor.opentelemetry.exporter.AzureMonitorTraceExporter", return_value=exporter
    ) as factory:
        tracing = RunTracing(
            tmp_path / "azure.jsonl", settings=settings, correlation_id="synthetic"
        )
        with tracing.tracer.start_as_current_span("azure"):
            pass
        tracing.close()
    assert tracing.export_status == "SENT_NOT_INGESTION_PROOF"
    assert factory.call_args.kwargs["disable_offline_storage"] is True
    assert factory.call_args.kwargs["tracer_provider"] is tracing.provider
    with patch(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
        return_value=InMemorySpanExporter(),
    ) as otlp:
        tracing = RunTracing(
            tmp_path / "otlp.jsonl", settings=azure(otlp_endpoint="http://127.0.0.1:4318/v1/traces")
        )
        with tracing.tracer.start_as_current_span("oss"):
            pass
        tracing.close()
    assert otlp.call_args.kwargs["timeout"] == 10
    for overrides in (
        {"otlp_endpoint": "http://untrusted.invalid"},
        {
            "export_monitor": True,
            "monitor_connection_string": connection,
            "otlp_endpoint": "http://127.0.0.1:4318/v1/traces",
        },
        {
            "export_monitor": True,
            "monitor_connection_string": "IngestionEndpoint=https://synthetic.in.applicationinsights.azure.us/",
        },
    ):
        with pytest.raises(ValueError):
            azure(**overrides)
    with pytest.raises(ValueError):
        Settings(otlp_endpoint="http://127.0.0.1:4318/v1/traces")


def test_real_monitor_exporter_constructs_with_supported_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in (
        "APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL",
        "APPLICATIONINSIGHTS_CONTROLPLANE_DISABLED",
        "APPLICATIONINSIGHTS_SDKSTATS_DISABLED",
    ):
        monkeypatch.setenv(key, "true")
    connection = (
        f"InstrumentationKey={uuid4()};"
        "IngestionEndpoint=https://synthetic.in.applicationinsights.azure.com/"
    )
    with patch("azure.monitor.opentelemetry.exporter.export._base.AzureMonitorClient") as client:
        tracing = RunTracing(
            tmp_path / "monitor-construction.jsonl",
            settings=azure(export_monitor=True, monitor_connection_string=connection),
        )
        try:
            assert client.call_args.kwargs["connection_timeout"] == 10
            assert client.call_args.kwargs["read_timeout"] == 10
        finally:
            tracing.close()


def test_export_failure_is_never_ingestion_success() -> None:
    delegate = MagicMock()
    delegate.export.return_value = SpanExportResult.FAILURE
    exporter = DeliveryExporter(delegate)
    assert exporter.status == "NOT_ATTEMPTED"
    assert exporter.export(()) == SpanExportResult.FAILURE
    assert exporter.status == "EXPORT_FAILED"
    delegate.export.side_effect = TimeoutError("synthetic transport failure")
    with pytest.raises(TimeoutError):
        exporter.export(())
    assert exporter.status == "EXPORT_FAILED"
    exporter.shutdown()
    delegate.shutdown.assert_called_once()


def test_workflow_remote_export_failure_is_explicit_and_retains_local_evidence(
    tmp_path: Path,
) -> None:
    delegate = MagicMock()
    delegate.export.return_value = SpanExportResult.FAILURE
    settings = azure(otlp_endpoint="http://127.0.0.1:4318/v1/traces")
    request = UserRequest(text="equipment policy", subject="synthetic-caller")
    with (
        patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
            return_value=delegate,
        ),
        pytest.raises(RuntimeError, match="Telemetry export failed"),
    ):
        run(
            request,
            tmp_path,
            mode="azure",
            settings=settings,
            model=lambda prompt: "Synthetic policy requires approval. [equipment-001]",
            retriever=LocalRetriever(),
            inspector=LocalInspector(),
        )
    records = (tmp_path / f"{request.correlation_id}.audit.jsonl").read_text()
    assert "telemetry-export-failed" in records
    assert (tmp_path / f"{request.correlation_id}.spans.jsonl").exists()


def test_log_analytics_readonly_empty_partial_and_scoped_rows() -> None:
    settings = azure(logs_workspace_id="synthetic-workspace")
    correlation = str(__import__("uuid").uuid4())
    query = MagicMock(return_value=LogsQueryResult(tables=[]))
    assert query_azure_traces(settings, correlation, query)["outcome"] == "INSUFFICIENT_EVIDENCE"
    assert "AppDependencies" in query.call_args.args[1]
    query.return_value = object()
    assert query_azure_traces(settings, correlation, query)["reason"] == "PARTIAL_OR_FAILED_QUERY"
    query.return_value = LogsQueryResult(
        tables=[
            LogsTable(
                name="synthetic",
                columns=["OperationId", "Name"],
                columns_types=["string", "string"],
                rows=[["synthetic-operation", "workflow"]],
            )
        ]
    )
    assert query_azure_traces(settings, correlation, query)["outcome"] == "PASS"
    with pytest.raises(ValueError):
        query_azure_traces(settings, "' or true", query)
    with pytest.raises(ValueError):
        query_azure_traces(Settings(), correlation, query)
    with (
        patch("foundry_security_accelerator.observability.DefaultAzureCredential"),
        patch("azure.monitor.query.LogsQueryClient") as client,
    ):
        client.return_value.__enter__.return_value.query_workspace.return_value = LogsQueryResult()
        assert query_azure_traces(settings, correlation)["outcome"] == "INSUFFICIENT_EVIDENCE"
        assert client.call_args.kwargs["endpoint"] == "https://api.loganalytics.io"


@pytest.mark.security
def test_tenant_bound_credential_enforces_requested_and_returned_tenant() -> None:
    source = MagicMock()
    payload = (
        base64.urlsafe_b64encode(json.dumps({"tid": "synthetic-tenant"}).encode())
        .decode()
        .rstrip("=")
    )
    source.get_token.return_value = AccessToken("header." + payload + ".signature", 9999999999)
    credential = TenantCredential(source, "synthetic-tenant")
    assert credential.get_token("scope") == source.get_token.return_value
    assert source.get_token.call_args.kwargs["tenant_id"] == "synthetic-tenant"
    with pytest.raises(PermissionError):
        credential.get_token("scope", tenant_id="other")
    with pytest.raises(PermissionError):
        TenantCredential(source, "other").get_token("scope")
    source.get_token.return_value = AccessToken("not-a-jwt", 9999999999)
    with pytest.raises(PermissionError):
        credential.get_token("scope")
    with pytest.raises(ValueError):
        TenantCredential(source, "")


def test_agent365_and_azure_cli_reports_stay_fail_closed(tmp_path: Path) -> None:
    with patch("foundry_security_accelerator.agent365.Settings", return_value=Settings()):
        assert agent365_main(["preflight"]) == 1
        assert agent365_main(["status"]) == 1
        assert agent365_main(["verify"]) == 1
        evidence = tmp_path / "empty.json"
        evidence.write_text("[]")
        assert agent365_main(["verify", "--evidence", str(evidence)]) == 1
    with pytest.raises(ValueError):
        resource_status(azure(account_name=""), preview_api=True)
    with (
        patch("foundry_security_accelerator.azure_ops.Settings", return_value=Settings()),
        patch(
            "foundry_security_accelerator.azure_ops.preflight",
            return_value=[{"check": "synthetic", "status": "VERIFICATION_REQUIRED"}],
        ),
    ):
        assert azure_main(["preflight"]) == 1
        assert azure_main(["provision"]) == 0
    with pytest.raises(ValueError):
        infrastructure(Settings(), "provision", authorized=True)
    with pytest.raises(ValueError):
        infrastructure(azure(), "unknown", authorized=True)
    with (
        patch(
            "foundry_security_accelerator.azure_ops.preflight", return_value=[{"status": "FAIL"}]
        ),
        pytest.raises(PermissionError),
    ):
        infrastructure(azure(), "provision", authorized=True)
