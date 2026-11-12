"""Cloud-specific, tenant-independent settings. Azure errors never select local mode."""

from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FSA_", env_file=".env", extra="forbid")

    mode: Literal["local", "azure"] = "local"
    cloud: Literal["AzureCloud", "AzureUSGovernment"] = "AzureCloud"
    tenant_id: str = ""
    subscription_id: str = ""
    resource_group: str = ""
    account_name: str = ""
    project_endpoint: str = ""
    model_deployment: str = ""
    agent_name: str = "security-policy-agent"
    agent_version: str = ""
    search_endpoint: str = ""
    search_index: str = ""
    content_safety_endpoint: str = ""
    content_safety_threshold: int = Field(default=4, ge=0, le=6)
    monitor_connection_string: SecretStr = SecretStr("")
    export_monitor: bool = False
    otlp_endpoint: str = ""
    logs_workspace_id: str = ""
    evaluation_endpoint: str = ""
    evaluation_deployment: str = ""
    evaluation_api_version: str = ""
    evaluation_threshold: int = Field(default=3, ge=1, le=5)

    @staticmethod
    def local() -> "Settings":
        """Ignore private dotenv and remote-export settings for explicit offline runs."""
        return _LocalSettings(mode="local", export_monitor=False, otlp_endpoint="")

    @property
    def logs_endpoint(self) -> str:
        return (
            "https://api.loganalytics.io"
            if self.cloud == "AzureCloud"
            else "https://api.loganalytics.us"
        )

    @property
    def authority(self) -> str:
        return (
            "https://login.microsoftonline.com"
            if self.cloud == "AzureCloud"
            else "https://login.microsoftonline.us"
        )

    @property
    def resource_manager(self) -> str:
        return (
            "https://management.azure.com"
            if self.cloud == "AzureCloud"
            else "https://management.usgovcloudapi.net"
        )

    @property
    def search_audience(self) -> str:
        return (
            "https://search.azure.com" if self.cloud == "AzureCloud" else "https://search.azure.us"
        )

    @property
    def cognitive_scope(self) -> str:
        return (
            "https://cognitiveservices.azure.com/.default"
            if self.cloud == "AzureCloud"
            else "https://cognitiveservices.azure.us/.default"
        )

    @property
    def project_scope(self) -> str:
        return (
            "https://ai.azure.com/.default"
            if self.cloud == "AzureCloud"
            else "https://ai.azure.us/.default"
        )

    def validate_endpoint(self, endpoint: str, suffix: str) -> None:
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith("." + suffix)
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.port not in (None, 443)
        ):
            raise ValueError(f"Endpoint must be an HTTPS host in selected cloud: {suffix}")

    @model_validator(mode="after")
    def validate_azure(self) -> Self:
        if self.mode == "local":
            if self.export_monitor or self.otlp_endpoint:
                raise ValueError("Local mode cannot export telemetry over the network")
            return self
        if not all(
            (self.tenant_id, self.subscription_id, self.project_endpoint, self.model_deployment)
        ):
            raise ValueError("Azure requires explicit tenant, subscription, project and model")
        commercial = self.cloud == "AzureCloud"
        suffix = "services.ai.azure.com" if commercial else "services.ai.azure.us"
        self.validate_endpoint(self.project_endpoint, suffix)
        if "/api/projects/" not in urlsplit(self.project_endpoint).path:
            raise ValueError("Expected a Foundry project endpoint, not an account endpoint")
        if not self.search_endpoint or not self.search_index:
            raise ValueError("Azure requires a governed Search endpoint and index")
        self.validate_endpoint(
            self.search_endpoint, "search.windows.net" if commercial else "search.azure.us"
        )
        if self.content_safety_endpoint:
            self.validate_endpoint(
                self.content_safety_endpoint,
                "cognitiveservices.azure.com" if commercial else "cognitiveservices.azure.us",
            )
        if self.export_monitor and not self.monitor_connection_string.get_secret_value():
            raise ValueError("Azure Monitor export requires a connection string")
        if self.export_monitor:
            parts = dict(
                segment.split("=", 1)
                for segment in self.monitor_connection_string.get_secret_value().split(";")
                if "=" in segment
            )
            ingestion = parts.get("IngestionEndpoint", "")
            self.validate_endpoint(
                ingestion,
                "in.applicationinsights.azure.com"
                if commercial
                else "in.applicationinsights.azure.us",
            )
        if self.export_monitor and self.otlp_endpoint:
            raise ValueError("Select exactly one remote telemetry destination")
        if self.otlp_endpoint:
            parsed = urlsplit(self.otlp_endpoint)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or (parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost"))
            ):
                raise ValueError("OTLP requires HTTPS, or explicit local-loopback HTTP")
        if self.evaluation_endpoint:
            self.validate_endpoint(
                self.evaluation_endpoint, "openai.azure.com" if commercial else "openai.azure.us"
            )
        return self


class _LocalSettings(Settings):
    model_config = SettingsConfigDict(env_file=None)
