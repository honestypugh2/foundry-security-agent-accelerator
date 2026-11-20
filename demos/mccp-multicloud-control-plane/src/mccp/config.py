"""Settings from environment variables (and an optional .env file). Secrets never live in code."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Fixed "today" for local mode so every run is deterministic (the demo day).
DEFAULT_DEMO_DATE = "2026-11-20"


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (KEY=VALUE lines). Existing environment variables always win."""
    path = path or REPO_ROOT / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    """All runtime configuration. Field names mirror the environment variable names."""

    mode: str = "local"
    # Azure API Management AI gateway
    apim_gateway_url: str = ""
    apim_resource_id: str = ""
    apim_api_path: str = "ai"
    apim_subscription_key: str = ""
    apim_api_version: str = "2024-05-01"
    # Microsoft Foundry
    foundry_project_endpoint: str = ""
    foundry_model_deployment: str = "policy-model"
    foundry_openai_api_version: str = "2025-04-01-preview"
    reasoning_effort: str = "minimal"  # gpt-5 family; set MCCP_REASONING_EFFORT= (empty) for non-reasoning models
    # Which identity provider the gateway trusts (matches the Bicep identityProvider parameter)
    identity_provider: str = "entra"
    # Okta (agent identity)
    okta_org_url: str = ""
    okta_issuer: str = ""
    okta_audience: str = "api://contoso-ai-gateway"
    okta_api_token: str = ""
    okta_client_id: str = ""
    okta_private_key_path: str = ""
    okta_key_id: str = ""
    okta_scopes: str = "ai.gateway.invoke"
    # ServiceNow (registry / system of record)
    servicenow_instance_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""
    servicenow_table: str = "x_ai_agent_registry"
    # Observability
    dd_api_key: str = ""
    dd_site: str = "datadoghq.com"
    otel_exporter_otlp_endpoint: str = ""
    applicationinsights_connection_string: str = ""
    log_analytics_workspace_id: str = ""
    # AWS
    aws_region: str = "us-east-1"
    # Local data / artifacts
    price_table_path: Path = field(default_factory=lambda: REPO_ROOT / "data" / "mccp" / "prices.json")
    data_dir: Path = field(default_factory=lambda: REPO_ROOT / "data" / "mccp")
    artifacts_dir: Path = field(default_factory=lambda: REPO_ROOT / "artifacts" / "mccp")
    demo_date: str = DEFAULT_DEMO_DATE

    @property
    def receipts_dir(self) -> Path:
        return self.artifacts_dir / "receipts"

    @property
    def is_local(self) -> bool:
        return self.mode == "local"

    @classmethod
    def from_env(cls, mode: str = "local", dotenv: bool = True) -> "Settings":
        if dotenv:
            # REPO_ROOT is this demo folder (demos/mccp-multicloud-control-plane), so both files are
            # found no matter which directory the command runs from.
            load_dotenv(REPO_ROOT / ".env")
            load_dotenv(REPO_ROOT / ".env.mccp.azure")  # written by infra/mccp/deploy.sh
        data_dir = Path(_env("MCCP_DATA_DIR") or REPO_ROOT / "data" / "mccp")
        return cls(
            mode=mode,
            apim_gateway_url=_env("APIM_GATEWAY_URL").rstrip("/"),
            apim_resource_id=_env("APIM_RESOURCE_ID").rstrip("/"),
            apim_api_path=_env("APIM_API_PATH", "ai").strip("/"),
            apim_subscription_key=_env("APIM_SUBSCRIPTION_KEY"),
            apim_api_version=_env("APIM_ARM_API_VERSION", "2024-05-01"),
            foundry_project_endpoint=_env("FOUNDRY_PROJECT_ENDPOINT"),
            foundry_model_deployment=_env("FOUNDRY_MODEL_DEPLOYMENT", "policy-model"),
            foundry_openai_api_version=_env("FOUNDRY_OPENAI_API_VERSION", "2025-04-01-preview"),
            reasoning_effort=os.environ.get("MCCP_REASONING_EFFORT", "minimal").strip(),
            identity_provider=_env("MCCP_IDENTITY_PROVIDER", "entra").lower(),
            okta_org_url=_env("OKTA_ORG_URL").rstrip("/"),
            okta_issuer=_env("OKTA_ISSUER").rstrip("/"),
            okta_audience=_env("OKTA_AUDIENCE", "api://contoso-ai-gateway"),
            okta_api_token=_env("OKTA_API_TOKEN"),
            okta_client_id=_env("OKTA_CLIENT_ID"),
            okta_private_key_path=_env("OKTA_PRIVATE_KEY_PATH"),
            okta_key_id=_env("OKTA_KEY_ID"),
            okta_scopes=_env("OKTA_SCOPES", "ai.gateway.invoke"),
            servicenow_instance_url=_env("SERVICENOW_INSTANCE_URL").rstrip("/"),
            servicenow_username=_env("SERVICENOW_USERNAME"),
            servicenow_password=_env("SERVICENOW_PASSWORD"),
            servicenow_table=_env("SERVICENOW_TABLE", "x_ai_agent_registry"),
            dd_api_key=_env("DD_API_KEY"),
            dd_site=_env("DD_SITE", "datadoghq.com"),
            otel_exporter_otlp_endpoint=_env("OTEL_EXPORTER_OTLP_ENDPOINT"),
            applicationinsights_connection_string=_env("APPLICATIONINSIGHTS_CONNECTION_STRING"),
            log_analytics_workspace_id=_env("LOG_ANALYTICS_WORKSPACE_ID"),
            aws_region=_env("AWS_REGION", "us-east-1"),
            price_table_path=Path(_env("MCCP_PRICE_TABLE") or data_dir / "prices.json"),
            data_dir=data_dir,
            artifacts_dir=Path(_env("MCCP_ARTIFACTS_DIR") or REPO_ROOT / "artifacts" / "mccp"),
            demo_date=_env("MCCP_DEMO_DATE", DEFAULT_DEMO_DATE),
        )

    def missing(self, *names: str) -> list[str]:
        """Return the env-var names (upper case) of any empty settings in ``names``."""
        return [n.upper() for n in names if not getattr(self, n)]
