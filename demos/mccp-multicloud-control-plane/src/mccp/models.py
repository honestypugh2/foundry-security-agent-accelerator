"""Core data model shared by every mccp module (stdlib dataclasses only)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Platform = Literal["foundry", "bedrock", "agentcore", "copilot_studio", "snowflake_cortex", "servicenow"]
Cloud = Literal["azure", "aws", "saas"]
AgentStatus = Literal["active", "throttled", "killed"]
KillScope = Literal["agent", "user", "global"]
ReceiptStatus = Literal["DRY_RUN", "SIMULATED", "APPLIED", "MANUAL", "SKIPPED", "FAILED"]

PLATFORMS: tuple[str, ...] = ("foundry", "bedrock", "agentcore", "copilot_studio", "snowflake_cortex", "servicenow")
CLOUDS: tuple[str, ...] = ("azure", "aws", "saas")
STATUSES: tuple[str, ...] = ("active", "throttled", "killed")

PLATFORM_CLOUD: dict[str, str] = {
    "foundry": "azure",
    "bedrock": "aws",
    "agentcore": "aws",
    "copilot_studio": "saas",
    "snowflake_cortex": "saas",
    "servicenow": "saas",
}


@dataclass
class AgentRecord:
    """One agent in the unified inventory (the 'single source of truth' row)."""

    agent_id: str
    name: str
    platform: str
    cloud: str
    owner: str
    cost_center: str
    okta_app_id: str = ""
    entra_agent_id: str = ""
    monthly_budget_usd: float = 0.0
    status: str = "active"
    model: str = ""
    description: str = ""
    sources: list[str] = field(default_factory=list)
    native_id: str = ""
    aws_role_name: str = ""
    apim_subscription_id: str = ""
    # True when the agent's model calls traverse the APIM AI gateway (enforceable at runtime).
    gateway_routed: bool = True
    last_access_review: str = ""

    def __post_init__(self) -> None:
        if self.platform not in PLATFORMS:
            raise ValueError(f"unknown platform {self.platform!r}; expected one of {PLATFORMS}")
        if self.cloud not in CLOUDS:
            raise ValueError(f"unknown cloud {self.cloud!r}; expected one of {CLOUDS}")
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}; expected one of {STATUSES}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRecord":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Budget:
    """Monthly dollar budget for an agent, user or cost center."""

    scope: Literal["agent", "user", "cost_center"]
    key: str
    monthly_limit_usd: float
    spend_mtd_usd: float = 0.0
    forecast_usd: float = 0.0
    status: Literal["ok", "warn", "breach"] = "ok"
    recommended_action: str = "none"

    @property
    def pct_used(self) -> float:
        return 0.0 if self.monthly_limit_usd <= 0 else 100.0 * self.spend_mtd_usd / self.monthly_limit_usd

    @property
    def pct_forecast(self) -> float:
        return 0.0 if self.monthly_limit_usd <= 0 else 100.0 * self.forecast_usd / self.monthly_limit_usd


@dataclass
class KillOrder:
    """A request to stop (or revive) agents. ``target`` is an agent id, a user id, or '*' for global."""

    scope: KillScope
    target: str
    reason: str
    requested_by: str
    revive: bool = False
    ticket: str = ""


@dataclass
class Receipt:
    """Evidence of one action at one enforcement point. Written as JSON under artifacts/mccp/receipts/."""

    action: str
    enforcement_point: str
    target: str
    status: ReceiptStatus
    mode: str
    detail: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    path: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        data.pop("path", None)
        return json.dumps(data, indent=2, sort_keys=True)
