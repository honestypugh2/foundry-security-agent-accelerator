"""Terminal presentation: ANSI colours and plain-text tables (stdlib only).

Colour language used everywhere:
  cyan  = context / narration      green = allowed / ok
  red   = denied / killed          amber = approval needed / limit reached
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterable, Sequence

_CODES = {
    "cyan": "36",
    "green": "32",
    "red": "31",
    "amber": "33",
    "magenta": "35",
    "blue": "34",
    "grey": "90",
    "bold": "1",
    "dim": "2",
}
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class Console:
    """Small printer that knows whether to emit ANSI colour."""

    def __init__(self, color: bool | None = None, stream: Any = None) -> None:
        self.stream = stream or sys.stdout
        if color is None:
            force = os.environ.get("FORCE_COLOR") or os.environ.get("MCCP_FORCE_COLOR")
            color = bool(force) or (hasattr(self.stream, "isatty") and self.stream.isatty())
            if os.environ.get("NO_COLOR"):
                color = False
        self.color = color

    def style(self, text: str, *styles: str) -> str:
        if not self.color or not styles:
            return text
        codes = ";".join(_CODES[s] for s in styles if s in _CODES)
        return f"\x1b[{codes}m{text}\x1b[0m"

    def print(self, text: str = "", *styles: str) -> None:
        print(self.style(text, *styles), file=self.stream)

    def scene(self, number: int, title: str, subtitle: str = "") -> None:
        bar = "═" * 78
        self.print()
        self.print(bar, "cyan")
        self.print(f" SCENE {number:02d} │ {title}", "cyan", "bold")
        if subtitle:
            self.print(f"          │ {subtitle}", "cyan")
        self.print(bar, "cyan")

    def say(self, text: str) -> None:
        self.print(f"  ▸ {text}", "cyan")

    def ok(self, text: str) -> None:
        self.print(f"  ✔ {text}", "green")

    def deny(self, text: str) -> None:
        self.print(f"  ✖ {text}", "red", "bold")

    def warn(self, text: str) -> None:
        self.print(f"  ◆ {text}", "amber")

    def note(self, text: str) -> None:
        self.print(f"    {text}", "grey")

    def table(self, headers: Sequence[str], rows: Iterable[Sequence[Any]], row_styles: Sequence[tuple[str, ...]] | None = None) -> None:
        for line in render_table(headers, rows, row_styles, self):
            print(line, file=self.stream)

    def json(self, data: Any, indent: int = 2, max_lines: int | None = None) -> None:
        lines = json.dumps(data, indent=indent, sort_keys=False, default=str).splitlines()
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines] + [f"  … ({len(lines) - max_lines} more lines)"]
        for line in lines:
            self.print(f"    {line}", "grey")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def render_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    row_styles: Sequence[tuple[str, ...]] | None = None,
    console: Console | None = None,
) -> list[str]:
    """Render a boxed table. Styles are applied per row after width calculation."""
    str_rows = [[_fmt(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    console = console or Console(color=False)

    def line(cells: Sequence[str]) -> str:
        return "  │ " + " │ ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " │"

    sep = "  ├─" + "─┼─".join("─" * w for w in widths) + "─┤"
    out = ["  ┌─" + "─┬─".join("─" * w for w in widths) + "─┐", console.style(line(list(headers)), "bold"), sep]
    for idx, row in enumerate(str_rows):
        styles = row_styles[idx] if row_styles and idx < len(row_styles) else ()
        out.append(console.style(line(row), *styles))
    out.append("  └─" + "─┴─".join("─" * w for w in widths) + "─┘")
    return out


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}"
    return str(value)


def status_style(status: str) -> tuple[str, ...]:
    """Map a status word to the shared colour language."""
    s = status.lower()
    if s in {"ok", "active", "allowed", "applied", "200"}:
        return ("green",)
    if s in {"warn", "throttled", "dry_run", "approval", "manual", "429", "403"}:
        return ("amber",)
    if s in {"breach", "killed", "denied", "failed", "423", "401", "503"}:
        return ("red",)
    return ()


def emit_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str, sort_keys=False))
