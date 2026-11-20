"""FinOps: spend per agent / user / cost center, month-to-date forecast, budget status, recommended action.

Prices come from data/mccp/prices.json (or MCCP_PRICE_TABLE) and are ILLUSTRATIVE.
Local mode reads data/mccp/usage_fixture.jsonl (+ calls made through the simulated gateway);
azure mode runs infra/mccp/kql/spend_month_to_date.kql against Log Analytics (azure-monitor-query).

Budget status:  ok < 80%  ·  warn 80–100%  ·  breach >= 100%   (month-to-date spend / monthly limit)
Recommended action: none · notify owner · approve increase · throttle · kill
"""

from __future__ import annotations

import calendar
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Literal

from mccp.config import REPO_ROOT, Settings
from mccp.models import AgentRecord, Budget

Scope = Literal["agent", "user", "cost_center"]
WARN_PCT = 80.0
BREACH_PCT = 100.0
SPIKE_FACTOR = 3.0  # last-3-day average vs. earlier average that marks a runaway


@dataclass
class UsageRecord:
    date: str
    agent_id: str
    user_id: str
    cost_center: str
    cloud: str
    platform: str
    model: str
    input_tokens: int
    output_tokens: int
    via_gateway: bool = True
    source: str = "SIMULATED"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class PriceTable:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.models: dict[str, dict[str, float]] = data["models"]
        self.label = data.get("label", "")

    @classmethod
    def load(cls, path: Path) -> "PriceTable":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        p = self.models.get(model)
        if p is None:
            raise KeyError(f"no price for model {model!r} in price table")
        return (input_tokens * p["input_per_1m"] + output_tokens * p["output_per_1m"]) / 1_000_000

    def blended_per_1m(self, model: str | None = None, input_share: float | None = None) -> float:
        model = model or self.data.get("reference_model_for_user_quota", "gpt-4.1")
        share = self.data.get("reference_input_share", 0.7) if input_share is None else input_share
        p = self.models[model]
        return share * p["input_per_1m"] + (1 - share) * p["output_per_1m"]

    def usd_to_tokens(self, usd: float, model: str | None = None) -> int:
        """Convert a dollar limit into the gateway token quota (rounded down to 100k)."""
        tokens = usd / self.blended_per_1m(model) * 1_000_000
        return int(tokens // 100_000 * 100_000)


def load_usage(path: Path) -> list[UsageRecord]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out.append(UsageRecord(**{k: row[k] for k in UsageRecord.__dataclass_fields__ if k in row}))  # type: ignore[attr-defined]
    return out


def load_budgets(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or REPO_ROOT / "data" / "mccp" / "budgets.json").read_text(encoding="utf-8"))


def records_from_metrics(metrics: Iterable[dict[str, Any]], agents: dict[str, AgentRecord], day: str) -> list[UsageRecord]:
    """Turn llm-emit-token-metric records (simulated or from App Insights) into usage records."""
    out = []
    for m in metrics:
        d = m["dimensions"]
        agent = agents.get(d["agent-id"])
        if agent is None:
            continue
        out.append(UsageRecord(date=day, agent_id=agent.agent_id, user_id=d["user-id"], cost_center=d["cost-center"],
                               cloud=d["cloud"], platform=agent.platform, model=agent.model,
                               input_tokens=int(m["Prompt Tokens"]), output_tokens=int(m["Completion Tokens"])))
    return out


@dataclass
class SpendLine:
    key: str
    spend_mtd_usd: float = 0.0
    tokens: int = 0
    daily_usd: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def spend_by(records: Iterable[UsageRecord], prices: PriceTable, scope: Scope) -> dict[str, SpendLine]:
    attr = {"agent": "agent_id", "user": "user_id", "cost_center": "cost_center"}[scope]
    lines: dict[str, SpendLine] = {}
    for r in records:
        key = getattr(r, attr)
        line = lines.setdefault(key, SpendLine(key))
        usd = prices.cost(r.model, r.input_tokens, r.output_tokens)
        line.spend_mtd_usd += usd
        line.tokens += r.total_tokens
        line.daily_usd[r.date] += usd
    return lines


def month_window(as_of: str) -> tuple[int, int]:
    """(elapsed full days before as_of, days in month). as_of is the demo morning, e.g. 2026-11-20."""
    d = date.fromisoformat(as_of)
    return max(1, d.day - 1), calendar.monthrange(d.year, d.month)[1]


def forecast(line: SpendLine, as_of: str) -> tuple[float, float, bool]:
    """Return (linear forecast, burn-rate forecast, spike flag).

    linear = MTD / elapsed * days_in_month (the spec'd forecast)
    burn   = MTD + avg(last 3 days) * remaining days (catches runaways the linear view hides)
    """
    elapsed, dim = month_window(as_of)
    linear = line.spend_mtd_usd / elapsed * dim
    as_of_d = date.fromisoformat(as_of)
    last3_days = [(as_of_d - timedelta(days=i)).isoformat() for i in (1, 2, 3)]
    last3 = sum(line.daily_usd.get(d, 0.0) for d in last3_days) / 3
    earlier_days = [d for d in line.daily_usd if d not in last3_days and d < as_of]
    earlier = sum(line.daily_usd[d] for d in earlier_days) / max(1, len(earlier_days))
    burn = line.spend_mtd_usd + last3 * (dim - elapsed)
    spike = earlier > 0 and last3 > SPIKE_FACTOR * earlier
    return linear, burn, spike


def budget_status(pct_used: float) -> Literal["ok", "warn", "breach"]:
    if pct_used >= BREACH_PCT:
        return "breach"
    if pct_used >= WARN_PCT:
        return "warn"
    return "ok"


def recommend(scope: Scope, status: str, pct_forecast: float, spike: bool) -> str:
    if status == "breach":
        if spike and scope == "agent":
            return "kill"
        return "approve increase" if scope == "user" else "throttle"
    if status == "warn":
        if scope == "user":
            return "approve increase" if pct_forecast >= 100 else "notify owner"
        return "throttle" if spike and pct_forecast >= 150 else "notify owner"
    return "notify owner" if pct_forecast >= 100 else "none"


@dataclass
class BudgetView:
    budget: Budget
    linear_forecast_usd: float
    burn_forecast_usd: float
    spike: bool
    tokens: int


def evaluate(records: list[UsageRecord], prices: PriceTable, limits: dict[str, float], scope: Scope, as_of: str) -> list[BudgetView]:
    lines = spend_by(records, prices, scope)
    views = []
    for key in sorted(set(limits) | set(lines)):
        line = lines.get(key, SpendLine(key))
        linear, burn, spike = forecast(line, as_of)
        fc = max(linear, burn)
        b = Budget(scope=scope, key=key, monthly_limit_usd=float(limits.get(key, 0.0)), spend_mtd_usd=round(line.spend_mtd_usd, 2),
                   forecast_usd=round(fc, 2))
        b.status = budget_status(b.pct_used) if b.monthly_limit_usd > 0 else "ok"
        b.recommended_action = recommend(scope, b.status, b.pct_forecast, spike) if b.monthly_limit_usd > 0 else "set a budget"
        views.append(BudgetView(b, round(linear, 2), round(burn, 2), spike, line.tokens))
    return views


def limits_for(scope: Scope, agents: list[AgentRecord], budgets: dict[str, Any]) -> dict[str, float]:
    if scope == "agent":
        return {a.agent_id: a.monthly_budget_usd for a in agents}
    if scope == "user":
        return dict(budgets["users"])
    return dict(budgets["cost_centers"])


def breach_alert_payload(view: BudgetView, agent: AgentRecord | None, as_of: str) -> dict[str, Any]:
    """Azure Monitor common alert schema (log search alert, abbreviated) as received by the kill-switch Logic App."""
    b = view.budget
    return {
        "schemaId": "azureMonitorCommonAlertSchema",
        "data": {
            "essentials": {
                "alertRule": f"mccp-budget-breach-{b.scope}",
                "severity": "Sev1" if b.status == "breach" else "Sev2",
                "signalType": "Log",
                "monitorCondition": "Fired",
                "firedDateTime": f"{as_of}T09:05:00Z",
                "description": f"{b.scope} {b.key} at {b.pct_used:.0f}% of ${b.monthly_limit_usd:,.0f} monthly budget (SIMULATED)",
            },
            "alertContext": {
                "condition": {
                    "allOf": [{
                        "metricMeasureColumn": "SpendUSD",
                        "operator": "GreaterThanOrEqual",
                        "threshold": str(b.monthly_limit_usd),
                        "metricValue": b.spend_mtd_usd,
                        "dimensions": [{"name": "agent", "value": b.key}] if b.scope == "agent" else [{"name": b.scope, "value": b.key}],
                    }]
                }
            },
            "customProperties": {
                "owner": agent.owner if agent else "",
                "cost_center": agent.cost_center if agent else "",
                "forecast_usd": b.forecast_usd,
                "runaway_spike": view.spike,
                "recommended_action": b.recommended_action,
            },
        },
    }


def datadog_webhook_payload(view: BudgetView) -> dict[str, Any]:
    """Shape of datadog/webhook_payload.json after Datadog substitutes its template variables."""
    return {
        "source": "datadog",
        "alert_id": "SIMULATED-1234567",
        "alert_title": f"[Triggered] mccp token budget {view.budget.key}",
        "alert_transition": "Triggered",
        "alert_scope": f"gen_ai.agent.id:{view.budget.key}",
        "agent_id": view.budget.key,
        "action": view.budget.recommended_action,
    }


def query_log_analytics(settings: Settings, kql_path: Path | None = None) -> list[UsageRecord]:
    """Azure mode: run spend_month_to_date.kql and return usage rows (model resolved via inventory later)."""
    try:
        from azure.identity import DefaultAzureCredential  # type: ignore
        from azure.monitor.query import LogsQueryClient  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pip install azure-monitor-query azure-identity") from exc
    if not settings.log_analytics_workspace_id:
        raise RuntimeError("LOG_ANALYTICS_WORKSPACE_ID is not set")
    kql = Path(kql_path or REPO_ROOT / "infra" / "mccp" / "kql" / "spend_month_to_date.kql").read_text(encoding="utf-8")
    today = date.today()
    start = today.replace(day=1)
    client = LogsQueryClient(DefaultAzureCredential())
    result = client.query_workspace(settings.log_analytics_workspace_id, kql, timespan=(start, today + timedelta(days=1)))
    out: list[UsageRecord] = []
    for table in getattr(result, "tables", []):
        cols = [c if isinstance(c, str) else c.name for c in table.columns]
        for row in table.rows:
            r = dict(zip(cols, row))
            out.append(UsageRecord(date=str(r["Day"])[:10], agent_id=r["AgentId"], user_id=r["UserId"], cost_center=r["CostCenter"],
                                   cloud=r["Cloud"], platform="", model="", input_tokens=int(r["PromptTokens"]),
                                   output_tokens=int(r["CompletionTokens"]), source="log-analytics"))
    return out


def attach_models(records: list[UsageRecord], agents: dict[str, AgentRecord]) -> list[UsageRecord]:
    for r in records:
        if not r.model and r.agent_id in agents:
            r.model = agents[r.agent_id].model
            r.platform = agents[r.agent_id].platform
    return [r for r in records if r.model]
