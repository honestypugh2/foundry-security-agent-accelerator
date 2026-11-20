"""Unified agent inventory across Azure, AWS and SaaS — one list, one schema (AgentRecord).

Adapters:
  FixtureAdapter  data/mccp/agents.json (local mode, and the enrichment source for owner / cost center / budget)
  FoundryAdapter  azure-ai-projects AIProjectClient(...).agents.list()  (azure mode)
  BedrockAdapter  boto3 'bedrock-agent' list_agents()                   (optional extra "aws")
  AgentCoreAdapter boto3 'bedrock-agentcore-control' list_agent_runtimes() (optional extra "aws"; VALIDATE)

ServiceNow (AI Control Tower) is the system of record; ``servicenow_payloads`` produces the rows that
servicenow.py upserts.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Protocol

from mccp.config import Settings
from mccp.models import CLOUDS, PLATFORMS, AgentRecord

try:  # optional: Azure
    from azure.ai.projects import AIProjectClient  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore
except ImportError:  # pragma: no cover - depends on environment
    AIProjectClient = None  # type: ignore[assignment,misc]
    DefaultAzureCredential = None  # type: ignore[assignment,misc]

try:  # optional: AWS extra
    import boto3  # type: ignore
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]


class AdapterUnavailable(RuntimeError):
    """Raised when an adapter's SDK or configuration is missing."""


class InventoryAdapter(Protocol):
    name: str

    def list_agents(self) -> list[AgentRecord]: ...


class FixtureAdapter:
    name = "fixture"

    def __init__(self, path: Path) -> None:
        self.path = path

    def list_agents(self) -> list[AgentRecord]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        agents = []
        for row in data["agents"]:
            rec = AgentRecord.from_dict(row)
            rec.sources = ["fixture"]
            agents.append(rec)
        return agents


class FoundryAdapter:
    """Lists agents in one Foundry project. Owner/cost center come from the fixture/CMDB merge."""

    name = "foundry"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_agents(self) -> list[AgentRecord]:
        if AIProjectClient is None or DefaultAzureCredential is None:
            raise AdapterUnavailable("pip install azure-ai-projects azure-identity  (FoundryAdapter)")
        if not self.settings.foundry_project_endpoint:
            raise AdapterUnavailable("FOUNDRY_PROJECT_ENDPOINT is not set")
        client = AIProjectClient(endpoint=self.settings.foundry_project_endpoint, credential=DefaultAzureCredential())
        # VALIDATE: azure-ai-projects 2.x exposes agents.list(); 1.0.x exposes agents.list_agents().
        lister = getattr(client.agents, "list", None) or getattr(client.agents, "list_agents")
        out = []
        for item in lister():
            native_id = str(getattr(item, "id", "") or getattr(item, "name", ""))
            name = str(getattr(item, "name", "") or native_id)
            out.append(AgentRecord(
                agent_id=_slug(name), name=name, platform="foundry", cloud="azure", owner="", cost_center="",
                native_id=native_id, sources=["foundry"]))
        return out


class BedrockAdapter:
    name = "bedrock"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_agents(self) -> list[AgentRecord]:
        if boto3 is None:
            raise AdapterUnavailable("pip install boto3  (optional extra 'aws')")
        client = boto3.client("bedrock-agent", region_name=self.settings.aws_region)
        out: list[AgentRecord] = []
        kwargs: dict[str, Any] = {}
        while True:
            resp = client.list_agents(**kwargs)
            for s in resp.get("agentSummaries", []):
                out.append(AgentRecord(
                    agent_id=_slug(s["agentName"]), name=s["agentName"], platform="bedrock", cloud="aws", owner="",
                    cost_center="", native_id=s["agentId"], sources=["bedrock"],
                    status="active" if s.get("agentStatus") in {"PREPARED", "NOT_PREPARED", "UPDATING", "VERSIONING"} else "throttled"))
            if not resp.get("nextToken"):
                return out
            kwargs["nextToken"] = resp["nextToken"]


class AgentCoreAdapter:
    name = "agentcore"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_agents(self) -> list[AgentRecord]:
        if boto3 is None:
            raise AdapterUnavailable("pip install boto3  (optional extra 'aws')")
        # VALIDATE: service name and response keys for Bedrock AgentCore control plane in your boto3 version.
        client = boto3.client("bedrock-agentcore-control", region_name=self.settings.aws_region)
        resp = client.list_agent_runtimes()
        return [
            AgentRecord(agent_id=_slug(r.get("agentRuntimeName", r.get("agentRuntimeId", ""))),
                        name=r.get("agentRuntimeName", ""), platform="agentcore", cloud="aws", owner="", cost_center="",
                        native_id=r.get("agentRuntimeId", ""), sources=["agentcore"])
            for r in resp.get("agentRuntimes", [])
        ]


def _slug(name: str) -> str:
    s = "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s if s.startswith("contoso-") else f"contoso-{s}"


def merge(*sources: Iterable[AgentRecord]) -> list[AgentRecord]:
    """Merge adapter results; dedupe by agent_id (then native_id). Earlier sources win non-empty fields."""
    by_id: dict[str, AgentRecord] = {}
    native_index: dict[str, str] = {}
    for source in sources:
        for rec in source:
            key = rec.agent_id
            if key not in by_id and rec.native_id and rec.native_id in native_index:
                key = native_index[rec.native_id]
            if key not in by_id:
                by_id[key] = replace(rec, sources=list(rec.sources))
            else:
                cur = by_id[key]
                for fname in cur.__dataclass_fields__:  # type: ignore[attr-defined]
                    if fname == "sources":
                        continue
                    if getattr(cur, fname) in ("", 0, 0.0, None) and getattr(rec, fname) not in ("", 0, 0.0, None):
                        setattr(cur, fname, getattr(rec, fname))
                cur.sources = sorted(set(cur.sources) | set(rec.sources))
            if rec.native_id:
                native_index[rec.native_id] = key
    return sorted(by_id.values(), key=lambda r: (CLOUDS.index(r.cloud), PLATFORMS.index(r.platform), r.agent_id))


def build_inventory(settings: Settings, live_adapters: list[InventoryAdapter] | None = None) -> tuple[list[AgentRecord], list[str]]:
    """Return (inventory, warnings). Local mode uses only the fixture; azure mode adds live adapters."""
    fixture = FixtureAdapter(settings.data_dir / "agents.json").list_agents()
    warnings: list[str] = []
    if settings.is_local:
        return merge(fixture), warnings
    adapters = live_adapters if live_adapters is not None else [FoundryAdapter(settings), BedrockAdapter(settings), AgentCoreAdapter(settings)]
    live: list[AgentRecord] = []
    for adapter in adapters:
        try:
            live.extend(adapter.list_agents())
        except AdapterUnavailable as exc:
            warnings.append(f"{adapter.name}: {exc}")
        except Exception as exc:  # live call failed — report, never fabricate
            warnings.append(f"{adapter.name}: live call failed: {exc}")
    return merge(fixture, live), warnings


def find(agents: list[AgentRecord], agent_id: str) -> AgentRecord:
    for a in agents:
        if a.agent_id == agent_id:
            return a
    raise KeyError(f"agent {agent_id!r} not in inventory")


def servicenow_payloads(agents: list[AgentRecord]) -> list[dict[str, Any]]:
    """Rows for the ServiceNow registry table. Column names are placeholders (u_*); VALIDATE with ServiceNow."""
    return [
        {
            "u_agent_id": a.agent_id,
            "u_name": a.name,
            "u_platform": a.platform,
            "u_cloud": a.cloud,
            "u_owner": a.owner,
            "u_cost_center": a.cost_center,
            "u_identity_okta_app_id": a.okta_app_id,
            "u_identity_entra_agent_id": a.entra_agent_id,
            "u_monthly_budget_usd": a.monthly_budget_usd,
            "u_status": a.status,
            "u_model": a.model,
            "u_gateway_routed": a.gateway_routed,
            "u_native_id": a.native_id,
            "u_last_access_review": a.last_access_review,
            "u_source": ",".join(a.sources),
        }
        for a in agents
    ]
