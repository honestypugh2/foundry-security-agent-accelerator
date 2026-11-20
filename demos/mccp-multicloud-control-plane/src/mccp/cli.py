"""Command line: `python -m mccp <command> [--mode local|azure] [--format text|json] [--authorize]`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mccp.config import REPO_ROOT, Settings
from mccp.demo import LocalRuntime, build_local_runtime, run_demo
from mccp.finops import (PriceTable, attach_models, breach_alert_payload, evaluate, limits_for, load_budgets, load_usage,
                         query_log_analytics)
from mccp.gateway import GatewayClient, gateway_token
from mccp.killswitch import KillSwitch, approve_quota_increase
from mccp.models import AgentRecord, KillOrder, Receipt
from mccp.policy_sim import XML_ELEMENT_MAP
from mccp.receipts import ReceiptWriter, utc_now_iso
from mccp.registry import build_inventory, find, servicenow_payloads
from mccp.report import Console, emit_json, status_style
from mccp.servicenow import ServiceNowClient

POLICY_XML = REPO_ROOT / "infra" / "mccp" / "policies" / "ai-gateway.xml"


# ── local state (so `kill` then `call` behave consistently across CLI invocations) ──────────
def _state_path(settings: Settings) -> Path:
    return settings.artifacts_dir / "local_state.json"


def _local_runtime(settings: Settings) -> LocalRuntime:
    rt = build_local_runtime(settings)
    path = _state_path(settings)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        for name, value in data.get("named_values", {}).items():
            rt.simulator.named_values.set(name, value)
        rt.simulator.suspended_subscriptions = set(data.get("suspended_subscriptions", []))
        for a in rt.agents:
            a.status = data.get("agent_status", {}).get(a.agent_id, a.status)
    return rt


def _save_local(rt: LocalRuntime) -> None:
    path = _state_path(rt.settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "simulated": True,
        "named_values": rt.simulator.named_values.as_dict(),
        "suspended_subscriptions": sorted(rt.simulator.suspended_subscriptions),
        "agent_status": {a.agent_id: a.status for a in rt.agents},
    }, indent=2) + "\n", encoding="utf-8")


def _writer(settings: Settings) -> ReceiptWriter:
    w = ReceiptWriter(settings.receipts_dir)
    if settings.receipts_dir.is_dir():
        w.seq = len(list(settings.receipts_dir.glob("*.json")))
    return w


def _print_receipts(c: Console, receipts: list[Receipt]) -> None:
    for r in receipts:
        style = {"SIMULATED": "green", "APPLIED": "green", "DRY_RUN": "amber", "MANUAL": "amber", "SKIPPED": "grey", "FAILED": "red"}[r.status]
        c.print(f"  {r.status:<9} {r.enforcement_point:<17} {r.action:<16} {r.target}", style)
        for step in r.detail.get("steps", []):
            c.note(f"          ↳ {step}")
        if r.path:
            c.note(f"          receipt: {r.path}")


# ── commands ───────────────────────────────────────────────────────────────────────────────
def cmd_demo(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    if settings.mode != "local":
        c.warn("The scripted demo is local-only (SIMULATED). Use the individual commands with --mode azure.")
        return 2
    if args.format == "json":
        import io

        summary = run_demo(settings, Console(color=False, stream=io.StringIO()))
        emit_json(summary)
    else:
        run_demo(settings, c)
    return 0


def cmd_inventory(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    agents, warnings = build_inventory(settings)
    if args.format == "json":
        emit_json({"mode": settings.mode, "simulated": settings.is_local, "warnings": warnings, "agents": [a.to_dict() for a in agents]})
        return 0
    c.say(f"Inventory ({settings.mode}{' · SIMULATED' if settings.is_local else ''}) — {len(agents)} agents")
    c.table(["agent", "platform", "cloud", "owner", "cost center", "okta app", "gateway", "status", "sources"],
            [[a.agent_id, a.platform, a.cloud, a.owner, a.cost_center, a.okta_app_id, a.gateway_routed, a.status, ",".join(a.sources)] for a in agents],
            [status_style(a.status) for a in agents])
    for w in warnings:
        c.warn(w)
    return 0


def cmd_sync(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    agents, _ = build_inventory(settings)
    receipts = ServiceNowClient(settings, _writer(settings)).upsert_agents(agents, authorize=args.authorize)
    if args.format == "json":
        emit_json({"payloads": servicenow_payloads(agents), "receipts": [r.path for r in receipts]})
    else:
        _print_receipts(c, receipts)
    return 0


def cmd_call(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    if settings.is_local:
        rt = _local_runtime(settings)
        result = rt.call(args.agent, args.user, args.prompt, max_tokens=args.max_tokens)
    else:
        agents, _ = build_inventory(settings)
        agent = find(agents, args.agent)
        token = gateway_token(settings, args.token)
        result = GatewayClient(settings).chat(agent, token, args.prompt, user_id=args.user, max_tokens=args.max_tokens)
    if args.format == "json":
        emit_json(result.__dict__)
    else:
        line = f"HTTP {result.status} {result.outcome} {result.error} · consumed={result.tokens_consumed} remaining_tpm={result.remaining_tokens} user_quota_left={result.user_remaining_quota}"
        (c.ok if result.status == 200 else c.warn if result.status in (403, 429) else c.deny)(line + (" [SIMULATED]" if result.simulated else ""))
    return 0 if result.status == 200 else 1


def _records_and_agents(settings: Settings) -> tuple[list[Any], list[AgentRecord], dict[str, Any]]:
    agents, _ = build_inventory(settings)
    budgets = load_budgets(settings.data_dir / "budgets.json")
    if settings.is_local:
        records = load_usage(settings.data_dir / "usage_fixture.jsonl")
    else:
        records = attach_models(query_log_analytics(settings), {a.agent_id: a for a in agents})
    return records, agents, budgets


def cmd_spend(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    records, agents, budgets = _records_and_agents(settings)
    prices = PriceTable.load(settings.price_table_path)
    as_of = settings.demo_date if settings.is_local else __import__("datetime").date.today().isoformat()
    views = evaluate(records, prices, limits_for(args.scope, agents, budgets), args.scope, as_of)
    if args.format == "json":
        emit_json({"scope": args.scope, "as_of": as_of, "prices": prices.label, "budgets": [
            {**v.budget.__dict__, "pct_used": round(v.budget.pct_used, 1), "linear_forecast_usd": v.linear_forecast_usd,
             "burn_forecast_usd": v.burn_forecast_usd, "spike": v.spike, "tokens": v.tokens} for v in views]})
        return 0
    c.say(f"Spend by {args.scope} · as of {as_of} · {prices.label[:70]}…")
    c.table([args.scope, "MTD", "limit", "used", "forecast", "spike", "status", "action"],
            [[v.budget.key, f"${v.budget.spend_mtd_usd:,.2f}", f"${v.budget.monthly_limit_usd:,.0f}", f"{v.budget.pct_used:.0f}%",
              f"${v.budget.forecast_usd:,.2f}", "yes" if v.spike else "", v.budget.status, v.budget.recommended_action] for v in views],
            [status_style(v.budget.status) for v in views])
    return 0


def cmd_alert_payload(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    records, agents, budgets = _records_and_agents(settings)
    prices = PriceTable.load(settings.price_table_path)
    views = evaluate(records, prices, limits_for("agent", agents, budgets), "agent", settings.demo_date)
    view = next(v for v in views if v.budget.key == args.agent)
    emit_json(breach_alert_payload(view, find(agents, args.agent), settings.demo_date))
    return 0


def _kill_or_revive(args: argparse.Namespace, settings: Settings, c: Console, revive: bool) -> int:
    scope, target = ("global", "*") if args.all else ("user", args.user) if args.user else ("agent", args.agent)
    if not target:
        c.deny("choose one of --agent, --user or --global")
        return 2
    rt = _local_runtime(settings) if settings.is_local else None
    agents = rt.agents if rt else build_inventory(settings)[0]
    order = KillOrder(scope=scope, target=target, reason=args.reason, requested_by=args.requested_by, revive=revive)  # type: ignore[arg-type]
    receipts = KillSwitch(settings, _writer(settings), rt.simulator if rt else None).execute(
        order, agents, authorize=args.authorize, timestamp=utc_now_iso(), hard=getattr(args, "hard", False))
    if rt and args.authorize:
        _save_local(rt)
    if args.format == "json":
        emit_json([json.loads(r.to_json()) | {"path": r.path} for r in receipts])
    else:
        c.say(f"{'Revive' if revive else 'Kill'} {scope}:{target} · authorize={args.authorize} · mode={settings.mode}")
        _print_receipts(c, receipts)
        if not args.authorize:
            c.warn("DRY_RUN only — re-run with --authorize to apply.")
    return 0


def cmd_approve(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    rt = _local_runtime(settings) if settings.is_local else None
    receipt = approve_quota_increase(settings, _writer(settings), args.user, args.authorize, args.approver, rt.simulator if rt else None, utc_now_iso())
    if rt and args.authorize:
        _save_local(rt)
    if args.format == "json":
        emit_json(json.loads(receipt.to_json()))
    else:
        _print_receipts(c, [receipt])
    return 0


def cmd_policy_map(args: argparse.Namespace, settings: Settings, c: Console) -> int:
    xml = POLICY_XML.read_text(encoding="utf-8")
    rows = [[tag, fn, "found" if tag.replace("&", "&amp;") in xml or tag in xml else "MISSING"] for tag, fn in XML_ELEMENT_MAP]
    if args.format == "json":
        emit_json([{"xml": r[0], "python": r[1], "status": r[2]} for r in rows])
    else:
        c.table(["ai-gateway.xml", "policy_sim.py", "check"], rows, [("green",) if r[2] == "found" else ("red",) for r in rows])
    return 0 if all(r[2] == "found" for r in rows) else 1


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--mode", choices=["local", "azure"], default="local", help="local = offline SIMULATED (default)")
    common.add_argument("--format", choices=["text", "json"], default="text")
    common.add_argument("--no-color", action="store_true")
    common.add_argument("--color", action="store_true", help="force ANSI colour even when not a TTY")

    p = argparse.ArgumentParser(prog="mccp", description="Multi-cloud AI agent control plane (Contoso Health demo)")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", parents=[common], help="end-to-end local story").set_defaults(func=cmd_demo)
    sub.add_parser("inventory", parents=[common], help="unified agent inventory").set_defaults(func=cmd_inventory)
    s = sub.add_parser("sync-servicenow", parents=[common], help="upsert inventory into ServiceNow")
    s.add_argument("--authorize", action="store_true")
    s.set_defaults(func=cmd_sync)
    s = sub.add_parser("call", parents=[common], help="one chat call through the AI gateway")
    s.add_argument("--agent", required=True)
    s.add_argument("--user", default="maria.gomez@contoso-health.example")
    s.add_argument("--prompt", default="Summarize claim CLM-0001.")
    s.add_argument("--max-tokens", type=int, default=256)
    s.add_argument("--token", default="", help="azure mode: bearer token (else Entra via az login, or Okta client credentials when MCCP_IDENTITY_PROVIDER=okta)")
    s.set_defaults(func=cmd_call)
    s = sub.add_parser("spend", parents=[common], help="spend, forecast and budget status")
    s.add_argument("--scope", choices=["agent", "user", "cost_center"], default="agent")
    s.set_defaults(func=cmd_spend)
    s = sub.add_parser("alert-payload", parents=[common], help="print the budget-breach alert payload for an agent")
    s.add_argument("--agent", default="contoso-rev-cycle-coder")
    s.set_defaults(func=cmd_alert_payload)
    for name, revive in (("kill", False), ("revive", True)):
        s = sub.add_parser(name, parents=[common], help=f"{name} an agent, a user or everything")
        g = s.add_mutually_exclusive_group(required=True)
        g.add_argument("--agent")
        g.add_argument("--user")
        g.add_argument("--global", dest="all", action="store_true")
        s.add_argument("--reason", default="manual kill-switch action")
        s.add_argument("--requested-by", default="ciso-office@contoso-health.example")
        s.add_argument("--authorize", action="store_true", help="apply changes (otherwise DRY_RUN receipts)")
        if not revive:
            s.add_argument("--hard", action="store_true", help="also suspend the agent's APIM subscription")
        s.set_defaults(func=lambda a, st, c, _r=revive: _kill_or_revive(a, st, c, _r))
    s = sub.add_parser("approve", parents=[common], help="approve a monthly quota increase for a user")
    s.add_argument("--user", required=True)
    s.add_argument("--approver", required=True)
    s.add_argument("--authorize", action="store_true")
    s.set_defaults(func=cmd_approve)
    sub.add_parser("policy-map", parents=[common], help="check simulator ↔ APIM XML mapping").set_defaults(func=cmd_policy_map)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env(mode=args.mode)
    color = True if args.color else (False if args.no_color else None)
    console = Console(color=color)
    try:
        return int(args.func(args, settings, console))
    except BrokenPipeError:  # output piped into `head` / `less` and closed early
        import os

        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except (RuntimeError, KeyError) as exc:
        console.deny(f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
