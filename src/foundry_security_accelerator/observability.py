from collections.abc import Sequence
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from typing import Protocol, TextIO, cast
from uuid import UUID

from azure.identity import DefaultAzureCredential
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace import Span as SDKSpan
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import Span, Tracer
from pydantic import TypeAdapter

from .config import Settings
from .contracts import Outcome
from .identity import TenantCredential


class CorrelationProcessor(SpanProcessor):
    def __init__(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id

    def on_start(self, span: SDKSpan, parent_context: Context | None = None) -> None:
        span.set_attribute("correlation.id", self.correlation_id)


class DeliveryExporter(SpanExporter):
    """Records export delivery outcome; never claims destination ingestion."""

    def __init__(self, exporter: SpanExporter) -> None:
        self.exporter = exporter
        self.failed = False
        self.attempted = False

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.attempted = True
        previous_failed = self.failed
        # If the SDK raises, the processor may catch it; delivery must still remain failed.
        self.failed = True
        result = self.exporter.export(spans)
        self.failed = previous_failed or result != SpanExportResult.SUCCESS
        return result

    def shutdown(self) -> None:
        self.exporter.shutdown()

    @property
    def status(self) -> str:
        if self.failed:
            return "EXPORT_FAILED"
        return "SENT_NOT_INGESTION_PROOF" if self.attempted else "NOT_ATTEMPTED"


class RunTracing:
    """Per-run JSON OTel export; no global provider replacement or remote exporter in local mode."""

    def __init__(
        self, path: Path, *, settings: Settings | None = None, correlation_id: str = ""
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file: TextIO = path.open("x", encoding="utf-8")
        self.provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": "foundry-security-accelerator",
                    "service.version": "0.1.0",
                }
            )
        )
        self.delivery: DeliveryExporter | None = None
        self.provider.add_span_processor(CorrelationProcessor(correlation_id))
        self.provider.add_span_processor(
            SimpleSpanProcessor(
                ConsoleSpanExporter(
                    out=self.file,
                    formatter=lambda span: span.to_json(indent=None) + "\n",
                )
            )
        )
        if settings is not None and settings.export_monitor:
            if settings.mode != "azure":
                raise ValueError("Remote traces require Azure mode")
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            self.delivery = DeliveryExporter(
                AzureMonitorTraceExporter(
                    connection_string=settings.monitor_connection_string.get_secret_value(),
                    tracer_provider=self.provider,
                    disable_offline_storage=True,
                    timeout=10,
                    read_timeout=10,
                    retry_total=0,
                )
            )
        elif settings is not None and settings.otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            self.delivery = DeliveryExporter(
                OTLPSpanExporter(
                    endpoint=settings.otlp_endpoint,
                    timeout=10,
                )
            )
        if self.delivery is not None:
            self.provider.add_span_processor(
                BatchSpanProcessor(
                    self.delivery,
                    max_queue_size=256,
                    max_export_batch_size=64,
                    schedule_delay_millis=1000,
                    export_timeout_millis=10000,
                )
            )
        self.tracer: Tracer = self.provider.get_tracer("foundry-security-accelerator", "0.1.0")

    def close(self) -> None:
        try:
            if not self.provider.force_flush(timeout_millis=15000):
                raise RuntimeError("Telemetry flush did not complete")
        finally:
            self.provider.shutdown()
            self.file.close()

    @property
    def export_status(self) -> str:
        return self.delivery.status if self.delivery is not None else "LOCAL_ONLY"


def traceparent(span: Span) -> str:
    context = span.get_span_context()
    return f"00-{context.trace_id:032x}-{context.span_id:016x}-{int(context.trace_flags):02x}"


def read_stage_names(path: Path) -> tuple[str, ...]:
    names: list[str] = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            record = TypeAdapter(dict[str, object]).validate_json(line)
            name = record.get("name")
            if not isinstance(name, str):
                raise ValueError("Invalid span evidence")
            names.append(name)
    return tuple(names)


class WorkspaceQuery(Protocol):
    def __call__(self, workspace_id: str, query: str, *, timespan: timedelta) -> object: ...


def query_azure_traces(
    settings: Settings, correlation_id: str, query: WorkspaceQuery | None = None
) -> dict[str, object]:
    if settings.mode != "azure" or not settings.logs_workspace_id:
        raise ValueError("Azure trace query requires Azure mode and a Log Analytics workspace ID")
    correlation = str(UUID(correlation_id))
    kql = (
        "union isfuzzy=true AppDependencies, AppRequests "
        f"| where tostring(Properties['correlation.id']) == '{correlation}' "
        "| project TimeGenerated, OperationId, Name, Success | take 50"
    )
    from azure.monitor.query import LogsQueryClient, LogsQueryResult

    with ExitStack() as stack:
        if query is None:
            source = stack.enter_context(DefaultAzureCredential(authority=settings.authority))
            client = stack.enter_context(
                LogsQueryClient(
                    TenantCredential(source, settings.tenant_id),
                    endpoint=settings.logs_endpoint,
                    audience=settings.logs_endpoint,
                    retry_total=2,
                    connection_timeout=15,
                    read_timeout=30,
                )
            )
            query = cast(WorkspaceQuery, client.query_workspace)
        result = query(settings.logs_workspace_id, kql, timespan=timedelta(hours=1))
    if not isinstance(result, LogsQueryResult):
        return {
            "outcome": Outcome.INSUFFICIENT_EVIDENCE.value,
            "reason": "PARTIAL_OR_FAILED_QUERY",
            "rows": [],
        }
    rows = [
        dict(zip(table.columns, row, strict=True)) for table in result.tables for row in table.rows
    ]
    return {
        "outcome": Outcome.PASS.value if rows else Outcome.INSUFFICIENT_EVIDENCE.value,
        "evidence_kind": "OBSERVED_LOG_ANALYTICS_ROWS",
        "rows": rows,
        "scope": "APPLICATION_TELEMETRY_NOT_AGENT365_DEFENDER_OR_PURVIEW_PROOF",
    }
