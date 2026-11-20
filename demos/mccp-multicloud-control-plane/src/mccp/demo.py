"""`mccp demo` — the end-to-end local story (offline, deterministic, SIMULATED).

Scenes: inventory → ServiceNow sync (dry run) → agent identity → 3 allowed calls → runaway agent burns the
user's monthly limit (429 burst, then 403 quota) → spend & forecast → breach alert + approval for more →
kill the runaway agent (423) → platform-wide stop drill (503) → revive (200) → summary.
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from mccp import ORG_NAME
from mccp.config import REPO_ROOT, Settings
from mccp.finops import (PriceTable, UsageRecord, breach_alert_payload, datadog_webhook_payload, evaluate, limits_for, load_budgets,
                         load_usage, records_from_metrics)
from mccp.gateway import CallResult, GatewayClient
from mccp.killswitch import KillSwitch, approve_quota_increase
from mccp.models import AgentRecord, KillOrder, Receipt
from mccp.okta import local_agent_token
from mccp.policy_sim import PolicyConfig, PolicySimulator, SimClock
from mccp.receipts import ReceiptWriter
from mccp.registry import build_inventory, find, servicenow_payloads
from mccp.report import Console, status_style
from mccp.servicenow import ServiceNowClient
from mccp.telemetry import LocalTelemetry, genai_attributes

ACCESS_REVIEW_MAX_DAYS = 90
SECURITY_LEAD = "ciso-office@contoso-health.example"


@dataclass
class LocalRuntime:
    settings: Settings
    agents: list[AgentRecord]
    prices: PriceTable
    budgets: dict[str, Any]
    usage: list[UsageRecord]
    simulator: PolicySimulator
    gateway: GatewayClient
    telemetry: LocalTelemetry = field(default_factory=LocalTelemetry)

    def token(self, agent: AgentRecord, user: str, **extra: Any) -> str:
        cfg = self.simulator.config
        return local_agent_token(agent, user, self.simulator.clock, cfg.okta_issuer, cfg.okta_audience, **extra)

    def call(self, agent_id: str, user: str, prompt: str, max_tokens: int = 256, **kw: Any) -> CallResult:
        agent = find(self.agents, agent_id)
        token = kw.pop("token", None) or self.token(agent, user)
        result = self.gateway.chat(agent, token, prompt, user_id=user, max_tokens=max_tokens, **kw)
        if result.status == 200:
            usage = result.body.get("usage", {})
            attrs = genai_attributes(agent, agent.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), user_id=user)
            with self.telemetry.span(f"chat {agent.model}", attrs, agent.cloud):
                pass
            self.telemetry.token_usage(attrs, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        return result


def build_local_runtime(settings: Settings) -> LocalRuntime:
    """Inventory + prices + fixture usage + a policy simulator whose counters hold month-to-date gateway usage."""
    agents, _ = build_inventory(settings)
    prices = PriceTable.load(settings.price_table_path)
    budgets = load_budgets(settings.data_dir / "budgets.json")
    usage = load_usage(settings.data_dir / "usage_fixture.jsonl")
    config = PolicyConfig(
        user_monthly_token_quota=prices.usd_to_tokens(budgets["standard_user_monthly_usd"]),
        user_tier2_monthly_token_quota=prices.usd_to_tokens(budgets["tier2_user_monthly_usd"]),
    )
    start = datetime.fromisoformat(f"{settings.demo_date}T09:00:00").replace(tzinfo=timezone.utc)
    sim = PolicySimulator(config=config, clock=SimClock(start))
    month = start.strftime("%Y-%m")
    for r in usage:
        if r.via_gateway and r.date.startswith(month):
            sim.quota_counters[(r.agent_id, month)] = sim.quota_counters.get((r.agent_id, month), 0) + r.total_tokens
            key = (f"user:{r.user_id}", month)
            sim.quota_counters[key] = sim.quota_counters.get(key, 0) + r.total_tokens
    return LocalRuntime(settings, agents, prices, budgets, usage, sim, GatewayClient(settings, sim))


def _status_line(c: Console, label: str, r: CallResult) -> None:
    detail = f"HTTP {r.status} {r.outcome}"
    if r.status == 200:
        c.ok(f"{label:<44} {detail} · {r.tokens_consumed:,} tokens · user quota left {r.user_remaining_quota:,}")
    elif r.status == 429 or (r.status == 403 and "quota" in r.error):
        extra = f" · retry in {r.retry_after}s" if r.retry_after else ""
        c.warn(f"{label:<44} {detail} · {r.error}{extra}")
    else:
        c.deny(f"{label:<44} {detail} · {r.error} ({r.decided_by})")


def run_demo(settings: Settings, console: Console | None = None) -> dict[str, Any]:
    c = console or Console()
    settings.mode = "local"
    receipts_dir = settings.receipts_dir / "demo"
    shown_dir = _rel(receipts_dir)
    shutil.rmtree(receipts_dir, ignore_errors=True)
    writer = ReceiptWriter(receipts_dir)
    rt = build_local_runtime(settings)
    sim, clock = rt.simulator, rt.simulator.clock
    ts = lambda: clock.now.isoformat()  # noqa: E731 - receipts carry simulated time for determinism
    calls: list[CallResult] = []

    def call(agent_id: str, user: str, prompt: str, label: str, **kw: Any) -> CallResult:
        r = rt.call(agent_id, user, prompt, **kw)
        calls.append(r)
        _status_line(c, label, r)
        return r

    # ── Scene 1 ────────────────────────────────────────────────────────────────────────────
    c.scene(1, f"{ORG_NAME} · Multi-cloud AI agent control plane", f"mode=local · SIMULATED · demo clock {clock.now:%Y-%m-%d %H:%M} UTC")
    c.say("Registry / system of record ... ServiceNow AI Control Tower")
    c.say("Agent identity ................ Okta (one service app per agent) + Entra Agent ID for Microsoft agents")
    c.say("Runtime enforcement ........... Azure API Management AI gateway (validate-jwt, llm-token-limit, kill lists)")
    c.say("Agent platform & control ...... Microsoft Foundry Control Plane (+ AWS Bedrock/AgentCore, Copilot Studio, Snowflake Cortex)")
    c.say("Observability ................. OpenTelemetry GenAI → Azure Monitor + Datadog")

    # ── Scene 2 ────────────────────────────────────────────────────────────────────────────
    c.scene(2, "One inventory: every agent, every cloud", "single source of truth, merged from platform adapters")
    as_of = date.fromisoformat(settings.demo_date)
    rows, styles, overdue = [], [], []
    for a in rt.agents:
        age = (as_of - date.fromisoformat(a.last_access_review)).days if a.last_access_review else 999
        review = f"{age}d ago" + (" ⚠" if age > ACCESS_REVIEW_MAX_DAYS else "")
        if age > ACCESS_REVIEW_MAX_DAYS:
            overdue.append(a.agent_id)
        rows.append([a.agent_id, a.platform, a.cloud, a.owner.split("@")[0], a.okta_app_id, "yes" if a.gateway_routed else "no",
                     f"${a.monthly_budget_usd:,.0f}", review])
        styles.append(("amber",) if age > ACCESS_REVIEW_MAX_DAYS else ())
    c.table(["agent", "platform", "cloud", "owner", "okta app", "gateway", "budget/mo", "access review"], rows, styles)
    clouds = Counter(a.cloud for a in rt.agents)
    c.say(f"{len(rt.agents)} agents · " + " · ".join(f"{k}={v}" for k, v in sorted(clouds.items())) +
          f" · {sum(not a.gateway_routed for a in rt.agents)} SaaS agents governed via identity + registry (no gateway path)")
    c.warn(f"Access review overdue (> {ACCESS_REVIEW_MAX_DAYS} days): {', '.join(overdue)} — agents are reviewed like teammates")

    # ── Scene 3 ────────────────────────────────────────────────────────────────────────────
    c.scene(3, "Sync to ServiceNow (system of record)", "Table API upsert · DRY_RUN unless --authorize in azure mode")
    sn = ServiceNowClient(settings, writer, ts())
    sn_receipts = sn.upsert_agents(rt.agents, authorize=False)
    c.json(servicenow_payloads([rt.agents[0]])[0], max_lines=8)
    c.warn(f"{len(sn_receipts)} DRY_RUN receipts → {shown_dir}/  (table '{settings.servicenow_table}' — VALIDATE with ServiceNow)")

    # ── Scene 4 ────────────────────────────────────────────────────────────────────────────
    c.scene(4, "Agents have identities: Okta tokens checked by the gateway", "validate-jwt (issuer, audience, expiry) + identity binding")
    claims_agent = find(rt.agents, "contoso-claims-triage")
    c.say(f"Okta access token for {claims_agent.agent_id}: iss={sim.config.okta_issuer} aud={sim.config.okta_audience} "
          f"cid={claims_agent.okta_app_id} ttl=15m")
    coder = find(rt.agents, "contoso-rev-cycle-coder")
    call("contoso-rev-cycle-coder", "j.chen@contoso-health.example", "summarize claim 1001", "impostor: coder token, header=claims-triage",
         header_overrides={"x-agent-id": "contoso-claims-triage"})
    bad = local_agent_token(coder, "j.chen@contoso-health.example", clock, sim.config.okta_issuer, "api://some-other-api")
    call("contoso-rev-cycle-coder", "j.chen@contoso-health.example", "hello", "token minted for another audience", token=bad)

    # ── Scene 5 ────────────────────────────────────────────────────────────────────────────
    c.scene(5, "Normal day: three agents, three clouds, one gateway", "OpenTelemetry GenAI span emitted per call")
    call("contoso-claims-triage", "maria.gomez@contoso-health.example", "Triage claim CLM-0001: knee MRI, prior auth missing." * 4,
         "azure  · claims-triage    · maria.gomez")
    call("contoso-patient-scheduling", "r.silva@contoso-health.example", "Find a cardiology slot next Tuesday morning." * 4,
         "aws    · patient-scheduling · r.silva")
    call("contoso-supply-forecast", "t.berg@contoso-health.example", "Forecast nitrile glove demand for December." * 4,
         "aws    · supply-forecast  · t.berg")
    span = rt.telemetry.spans[0]
    c.note("span " + span["name"] + " " + ", ".join(f"{k}={v}" for k, v in span["attributes"].items() if k.startswith("gen_ai.")))

    # ── Scene 6 ────────────────────────────────────────────────────────────────────────────
    jchen = "j.chen@contoso-health.example"
    used = sim.quota_used(f"user:{jchen}")
    c.scene(6, "Runaway: rev-cycle-coder loops on behalf of j.chen", f"user limit $40/mo ≈ {sim.config.user_monthly_token_quota:,} tokens · "
            f"already used {used:,} · TPM/agent {sim.config.tpm_per_agent:,}")
    loop_prompt = "Re-code encounter ENC-7781 and re-check every modifier. " * 420
    n, throttles = 0, 0
    while n < 20:
        n += 1
        r = call("contoso-rev-cycle-coder", jchen, loop_prompt, f"loop #{n:02d}", max_tokens=1024)
        if r.status == 429:
            throttles += 1
            c.note(f"gateway burst limit hit → agent backs off; demo clock +60s ({clock.now:%H:%M} → next minute)")
            clock.advance(60)
        elif r.status != 200:
            break
    c.warn("Monthly per-user limit reached: the gateway now refuses j.chen's traffic until approval or month end")

    # ── Scene 7 ────────────────────────────────────────────────────────────────────────────
    c.scene(7, "Spend, forecast and budget status", f"prices ILLUSTRATIVE · MTD as of {settings.demo_date} · ok <80% · warn 80-100% · breach ≥100%")
    today_records = records_from_metrics(sim.metrics, {a.agent_id: a for a in rt.agents}, settings.demo_date)
    records = rt.usage + today_records
    agent_views = evaluate(records, rt.prices, limits_for("agent", rt.agents, rt.budgets), "agent", settings.demo_date)
    rows, styles = [], []
    for v in agent_views:
        b = v.budget
        rows.append([b.key, f"${b.spend_mtd_usd:,.2f}", f"${b.monthly_limit_usd:,.0f}", f"{int(b.pct_used)}%", f"${b.forecast_usd:,.2f}",
                     "▲ spike" if v.spike else "", b.status, b.recommended_action])
        styles.append(status_style(b.status))
    c.table(["agent", "MTD", "budget", "used", "forecast", "trend", "status", "action"], rows, styles)
    user_views = sorted(evaluate(records, rt.prices, limits_for("user", rt.agents, rt.budgets), "user", settings.demo_date),
                        key=lambda v: -v.budget.pct_used)[:3]
    rows = [[v.budget.key, f"${v.budget.spend_mtd_usd:,.2f}", f"${v.budget.monthly_limit_usd:,.0f}", f"{v.budget.pct_used:.1f}%",
             v.budget.status, v.budget.recommended_action] for v in user_views]
    c.table(["top users", "MTD", "limit", "used", "status", "action"], rows, [status_style(v.budget.status) for v in user_views])

    # ── Scene 8 ────────────────────────────────────────────────────────────────────────────
    c.scene(8, "Alerts route to action: approval for people, kill for runaways", "Azure Monitor alert + Datadog monitor → Logic App")
    coder_view = next(v for v in agent_views if v.budget.key == coder.agent_id)
    alert = breach_alert_payload(coder_view, coder, settings.demo_date)
    c.json({"essentials": {k: alert["data"]["essentials"][k] for k in ("alertRule", "severity", "description")},
            "dimensions": alert["data"]["alertContext"]["condition"]["allOf"][0]["dimensions"],
            "recommended_action": alert["data"]["customProperties"]["recommended_action"]})
    c.note(f"Datadog webhook → same Logic App: alert_scope={datadog_webhook_payload(coder_view)['alert_scope']}")
    c.warn(f"Approval request: {jchen} asks for more (limit $40 → $80). Approver: cost-center owner k.ito")
    appr = approve_quota_increase(settings, writer, jchen, authorize=True, approver="k.ito@contoso-health.example", simulator=sim, timestamp=ts())
    c.ok(f"Approved → named value quota-tier2-users = {appr.detail['new']}  [{appr.status}]")
    call("contoso-claims-triage", jchen, "Draft appeal letter for denied claim CLM-0042.", "j.chen via claims-triage (approved tier)")

    # ── Scene 9 ────────────────────────────────────────────────────────────────────────────
    c.scene(9, "Kill switch: stop the runaway agent everywhere", "order: ① gateway (seconds) → ② identity → ③ record → platform steps")
    ks = KillSwitch(settings, writer, sim)
    order = KillOrder(scope="agent", target=coder.agent_id, reason="runaway spend: budget breach with 3-day spike",
                      requested_by=SECURITY_LEAD, ticket="SIM-CHG-0001")
    kill_receipts = ks.execute(order, rt.agents, authorize=True, timestamp=ts())
    _print_receipts(c, kill_receipts)
    call("contoso-rev-cycle-coder", "p.nair@contoso-health.example", "Code encounter ENC-9001.", "rev-cycle-coder after kill (p.nair)")
    call("contoso-claims-triage", "maria.gomez@contoso-health.example", "Triage claim CLM-0002.", "claims-triage keeps working (maria)")

    # ── Scene 10 ───────────────────────────────────────────────────────────────────────────
    c.scene(10, "Platform-wide stop drill (global scope)", "one named value flips every agent behind the gateway to 503")
    g = KillOrder(scope="global", target="*", reason="quarterly kill-switch drill", requested_by=SECURITY_LEAD)
    g_receipts = ks.execute(g, rt.agents, authorize=True, timestamp=ts())
    call("contoso-patient-scheduling", "r.silva@contoso-health.example", "Book follow-up.", "patient-scheduling during global stop")
    g_receipts += ks.execute(KillOrder(scope="global", target="*", reason="drill complete", requested_by=SECURITY_LEAD, revive=True),
                             rt.agents, authorize=True, timestamp=ts())
    c.ok("Drill reverted: killswitch-global = " + sim.named_values.killswitch_global)

    # ── Scene 11 ───────────────────────────────────────────────────────────────────────────
    c.scene(11, "Revive after the fix", "same enforcement points, reversed")
    clock.advance(3600)
    revive_receipts = ks.execute(KillOrder(scope="agent", target=coder.agent_id, reason="loop fixed in v1.4.2", requested_by=SECURITY_LEAD,
                                           revive=True), rt.agents, authorize=True, timestamp=ts())
    _print_receipts(c, revive_receipts)
    call("contoso-rev-cycle-coder", "p.nair@contoso-health.example", "Code encounter ENC-9001.", "rev-cycle-coder after revive (p.nair)")

    # ── Scene 12 ───────────────────────────────────────────────────────────────────────────
    c.scene(12, "Summary", "visibility · governance · cost limits · kill switch")
    by_status = Counter(r.status for r in calls)
    c.table(["HTTP", "meaning", "calls"], [[s, _meaning(s), n] for s, n in sorted(by_status.items())],
            [status_style(str(s)) for s, _ in sorted(by_status.items())])
    c.say(f"Receipts written: {len(writer.receipts)} → {shown_dir}/")
    c.say(f"Token metric records (llm-emit-token-metric, SIMULATED): {len(sim.metrics)} · OTel spans: {len(rt.telemetry.spans)}")
    c.note("SIMULATED: gateway decisions, tokens, spend. DRY_RUN: ServiceNow, Okta, AWS IAM. Nothing left this machine.")
    c.print("  Next: `--mode azure` with --authorize after deploying infra/mccp (see docs/mccp/PLAN.md).", "bold")

    return {
        "mode": "local",
        "simulated": True,
        "agents": len(rt.agents),
        "calls": [{"agent": r.agent_id, "user": r.user_id, "status": r.status, "outcome": r.outcome, "error": r.error} for r in calls],
        "status_counts": {str(k): v for k, v in sorted(by_status.items())},
        "throttles": throttles,
        "receipts": [r.path for r in writer.receipts],
        "metrics": len(sim.metrics),
        "agent_budgets": [{"agent": v.budget.key, "status": v.budget.status, "action": v.budget.recommended_action,
                           "spend_mtd_usd": v.budget.spend_mtd_usd} for v in agent_views],
        "named_values": sim.named_values.as_dict(),
    }


def _meaning(status: int) -> str:
    return {200: "allowed", 401: "unauthenticated (identity)", 403: "forbidden / monthly quota", 423: "killed (kill switch)",
            429: "burst limit (TPM)", 503: "global stop"}.get(status, "other")


def _print_receipts(c: Console, receipts: list[Receipt]) -> None:
    for r in receipts:
        style = {"SIMULATED": "green", "APPLIED": "green", "DRY_RUN": "amber", "MANUAL": "amber", "SKIPPED": "grey", "FAILED": "red"}[r.status]
        what = r.detail.get("named_value", "") and f"{r.detail['named_value']}={r.detail['new']}"
        what = what or r.request.get("url", "") or r.request.get("api", "") or r.request.get("write", "") or r.detail.get("reason", "")
        c.print(f"  {r.status:<9} {r.enforcement_point:<17} {r.action:<19} {str(what)[:84]}", style)
        for step in r.detail.get("steps", [])[:2]:
            c.note(f"          ↳ {step[:100]}")


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def run_demo_capture(settings: Settings, color: bool = False) -> tuple[str, dict[str, Any]]:
    buf = io.StringIO()
    summary = run_demo(settings, Console(color=color, stream=buf))
    return buf.getvalue(), summary
