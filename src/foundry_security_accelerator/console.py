"""Terminal views of recorded results; rendering never invokes services or tools."""

import re
import textwrap
from collections.abc import Mapping

from pydantic import TypeAdapter

from .security import redact

_RECORDS = TypeAdapter(list[dict[str, object]])
_STRINGS = TypeAdapter(list[str])
_ESCAPES = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
_COLORS = {"cyan": "1;36", "green": "1;32", "red": "1;31", "amber": "1;33"}


def _text(value: object) -> str:
    text = _ESCAPES.sub("", redact(str(value)))
    return " ".join("".join(c if c.isprintable() else " " for c in text).split())


def _tone(status: object) -> str:
    if status in ("PASS", "ANSWERED", "READ_ONLY", "ALLOW", "VERIFIED"):
        return "green"
    if status in ("DENIED", "BLOCKED", "DENY", "FAIL", "FAILED"):
        return "red"
    return "amber"


def render_demo(
    report: Mapping[str, object],
    *,
    mode: str,
    question: str,
    color: bool,
    width: int = 100,
) -> str:
    """Render actual decisions, without promoting workflow success to integration proof."""
    lines: list[str] = []
    width = max(40, width)

    def paint(text: str, tone: str) -> str:
        return f"\033[{_COLORS[tone]}m{text}\033[0m" if color else text

    def field(label: str, value: object, tone: str | None = None) -> None:
        wrapped = textwrap.wrap(
            _text(value),
            width=width,
            initial_indent=f"  {label:<10}: ",
            subsequent_indent=" " * 14,
        )
        lines.extend(paint(line, tone) if tone else line for line in wrapped)

    def scene(item: Mapping[str, object]) -> None:
        lines.append("")
        status = item["status"]
        label = f"{_text(item['scene_id'])} | " if "scene_id" in item else ""
        lines.append(paint(label, "cyan") + paint(_text(status), _tone(status)))
        field("ask", item.get("question", question))
        if "agent_ceiling" in item:
            sets = [
                "{" + ",".join(_STRINGS.validate_python(item[key])) + "}"
                for key in ("agent_ceiling", "user_classifications", "effective_classifications")
            ]
            field("identity", f"agent {sets[0]} & user {sets[1]} -> effective {sets[2]}")
        for tool in _RECORDS.validate_python(item.get("tool_calls", [])):
            executed = "EXECUTED" if tool["executed"] is True else "not executed"
            status = tool["status"]
            decision = (
                "ALLOW" if status == "READ_ONLY" else "DENY" if status == "BLOCKED" else status
            )
            field(
                "tool",
                f"{tool['name']} -> {decision} {tool['rule_id']} ({executed})",
                _tone(status),
            )
        for section in _RECORDS.validate_python(item.get("quarantined_sections", [])):
            field(
                "shields",
                f"{section['rule_id']} QUARANTINED {section['source_id']} {section['section_id']}",
                "amber",
            )
        if "answer" in item:
            field("answer", item["answer"])
        field(
            "outcome",
            " | ".join(_text(item[key]) for key in ("status", "rule_id", "reason") if key in item),
            _tone(item["status"]),
        )
        if "approval_id" in item:
            field("approval", item["approval_id"], "amber")
            field("expires", item["expires_at"], "amber")
        if "audit_verified" in item:
            audit_status = "VERIFIED" if item["audit_verified"] is True else "FAILED"
            field("audit", audit_status, _tone(audit_status))

    lines.append(paint("FOUNDRY SECURITY | PROTECT / PROVE / OPERATE", "cyan"))
    field(
        "execution",
        "LOCAL - synthetic fixtures; no Azure calls; synthetic role labels"
        if mode == "local"
        else (
            "AZURE - live presentation function tools; synthetic data; roles are NOT Entra OBO"
            if report.get("kind") == "AZURE_LIVE_PRESENTATION_SYNTHETIC_DATA"
            else "AZURE - live equipment workflow; synthetic request data"
        ),
        "cyan",
    )
    lines.append(paint("-" * min(width, 100), "cyan"))
    if "scenes" in report:
        for item in _RECORDS.validate_python(report["scenes"]):
            scene(item)
        lines.append("")
        field("demo", report["status"], _tone(report["status"]))
    elif "kind" in report:
        scene(report)
    else:
        lines.append("")
        field("ask", question)
        if "tool_name" in report:
            field(
                "tool",
                f"{report['tool_name']} -> {report['tool_status']}",
                _tone(report["tool_status"]),
            )
        if "sources" in report:
            field("sources", report["sources"], "cyan")
        if "policy_outcome" in report:
            field(
                "policy",
                f"{report['policy_outcome']} | {report['policy_reason']}",
                _tone(report["policy_outcome"]),
            )
        field("answer", report["answer"])
        field("outcome", report["status"], _tone(report["status"]))
        for label, key in (
            ("telemetry", "telemetry_export"),
            ("run", "correlation_id"),
            ("audit", "audit"),
            ("audit head", "audit_head"),
            ("traces", "traces"),
        ):
            if key in report:
                field(label, report[key])
    if report.get("business_action_executed") is False or report["status"] == "AWAITING_APPROVAL":
        field("business", "NOT EXECUTED", "amber")
    elif report["status"] == "DRY_RUN":
        field("business", "DRY_RUN receipt only; no business system changed", "amber")
    if "manifest_path" in report:
        field("evidence", report["manifest_path"])
    if mode == "azure":
        field("boundary", "Not proof of IQ retrieval, Monitor ingestion or Agent 365 integration")
    return "\n".join(lines)
