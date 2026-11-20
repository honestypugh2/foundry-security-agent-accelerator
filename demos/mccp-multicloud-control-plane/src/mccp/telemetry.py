"""OpenTelemetry with GenAI semantic conventions; dual export to Azure Monitor and Datadog (OTLP).

Azure mode (when the SDKs are installed):
  TracerProvider/MeterProvider with
    - AzureMonitorTraceExporter / AzureMonitorMetricExporter (APPLICATIONINSIGHTS_CONNECTION_STRING)
    - OTLPSpanExporter / OTLPMetricExporter over HTTP to a Datadog Agent or OTel Collector
      (OTEL_EXPORTER_OTLP_ENDPOINT, e.g. http://localhost:4318) — see otel/collector-config.yaml
Local mode: a stdlib recorder that prints spans as JSON (no third-party packages).

GenAI attributes follow the OpenTelemetry GenAI semantic conventions (status: Development).
VALIDATE attribute names against the semconv version your collector / Datadog / Azure Monitor expect
(e.g. gen_ai.system was renamed gen_ai.provider.name in newer versions).
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from mccp import __version__
from mccp.config import Settings
from mccp.models import AgentRecord

SERVICE_NAME = "mccp-agents"

CLOUD_PROVIDER = {"azure": "azure", "aws": "aws", "saas": "saas"}  # semconv cloud.provider values: azure, aws, gcp, …


def genai_attributes(agent: AgentRecord, model: str, input_tokens: int, output_tokens: int, operation: str = "chat",
                     user_id: str = "") -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "gen_ai.operation.name": operation,
        "gen_ai.request.model": model,
        "gen_ai.usage.input_tokens": input_tokens,
        "gen_ai.usage.output_tokens": output_tokens,
        "gen_ai.agent.id": agent.agent_id,
        "gen_ai.agent.name": agent.name,
        "mccp.platform": agent.platform,
        "mccp.cost_center": agent.cost_center,
    }
    if user_id:
        attrs["enduser.id"] = user_id  # VALIDATE: PII policy — hash or drop if user ids must not leave the tenant
    return attrs


def resource_attributes(cloud: str = "azure") -> dict[str, Any]:
    return {
        "service.name": SERVICE_NAME,
        "service.version": __version__,
        "cloud.provider": CLOUD_PROVIDER.get(cloud, cloud),
        "deployment.environment": "demo",
        "organization": "contoso-health",
    }


@dataclass
class LocalTelemetry:
    """Stdlib recorder that mimics a console span exporter (SIMULATED)."""

    spans: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    exporters: tuple[str, ...] = ("console (SIMULATED)",)

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any], cloud: str = "azure") -> Iterator[dict[str, Any]]:
        record = {"name": name, "kind": "CLIENT", "resource": resource_attributes(cloud), "attributes": dict(attributes)}
        yield record
        self.spans.append(record)

    def token_usage(self, attributes: dict[str, Any], input_tokens: int, output_tokens: int) -> None:
        for token_type, value in (("input", input_tokens), ("output", output_tokens)):
            self.metrics.append({"name": "gen_ai.client.token.usage", "value": value,
                                 "attributes": {**attributes, "gen_ai.token.type": token_type}})

    def dump(self, last: int = 1) -> str:
        return json.dumps(self.spans[-last:], indent=2)


class OTelTelemetry:
    """Real OpenTelemetry SDK pipeline with Azure Monitor + OTLP exporters."""

    def __init__(self, settings: Settings, cloud: str = "azure") -> None:
        try:
            from opentelemetry import metrics, trace  # type: ignore
            from opentelemetry.sdk.metrics import MeterProvider  # type: ignore
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader  # type: ignore
            from opentelemetry.sdk.resources import Resource  # type: ignore
            from opentelemetry.sdk.trace import TracerProvider  # type: ignore
            from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
        except ImportError as exc:
            raise RuntimeError("pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http azure-monitor-opentelemetry") from exc

        resource = Resource.create(resource_attributes(cloud))
        tracer_provider = TracerProvider(resource=resource)
        readers = []
        self.exporters: list[str] = []
        if settings.applicationinsights_connection_string:
            from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter, AzureMonitorTraceExporter  # type: ignore

            cs = settings.applicationinsights_connection_string
            tracer_provider.add_span_processor(BatchSpanProcessor(AzureMonitorTraceExporter(connection_string=cs)))
            readers.append(PeriodicExportingMetricReader(AzureMonitorMetricExporter(connection_string=cs)))
            self.exporters.append("azure-monitor")
        if settings.otel_exporter_otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter  # type: ignore
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore

            base = settings.otel_exporter_otlp_endpoint.rstrip("/")
            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces")))
            readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{base}/v1/metrics")))
            self.exporters.append("otlp (Datadog Agent / OTel Collector)")
        if not self.exporters:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor  # type: ignore

            tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            self.exporters.append("console")
        trace.set_tracer_provider(tracer_provider)
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=readers))
        self.tracer = trace.get_tracer("mccp")
        meter = metrics.get_meter("mccp")
        self.histogram = meter.create_histogram("gen_ai.client.token.usage", unit="{token}", description="Tokens used per GenAI call")

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any], cloud: str = "azure") -> Iterator[Any]:
        with self.tracer.start_as_current_span(name, attributes=attributes) as span:
            yield span

    def token_usage(self, attributes: dict[str, Any], input_tokens: int, output_tokens: int) -> None:
        self.histogram.record(input_tokens, {**attributes, "gen_ai.token.type": "input"})
        self.histogram.record(output_tokens, {**attributes, "gen_ai.token.type": "output"})


def setup_telemetry(settings: Settings, cloud: str = "azure") -> LocalTelemetry | OTelTelemetry:
    if settings.is_local:
        return LocalTelemetry()
    return OTelTelemetry(settings, cloud)
