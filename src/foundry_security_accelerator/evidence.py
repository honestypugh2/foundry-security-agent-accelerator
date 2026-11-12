"""Honest evidence inventory; saved files are not authenticated platform observations."""

from pathlib import Path
from typing import Literal


def evidence_pack(state_dir: Path, mode: Literal["local", "azure"]) -> str:
    report = state_dir / "reports" / "redteam-reconciliation.json"
    redteam = (
        "SAVED REPORT PRESENT (NOT VERIFIED)" if report.is_file() else "NOT OBSERVED IN THIS MODE"
    )
    registry = "NOT CHECKED HERE" if mode == "azure" else "NOT OBSERVED IN THIS MODE"
    return (
        "# Evidence pack\n\n"
        f"Execution mode: {mode}. This inventory makes no live observation.\n\n"
        "| Evidence | Status | Scope |\n"
        "|---|---|---|\n"
        "| Application audit / traces | NOT CHECKED HERE | "
        "Verify actual run paths and retained head |\n"
        "| Foundry service execution / evaluation | NOT CHECKED HERE | "
        "Installed adapters are not observed execution |\n"
        f"| Agent 365 registry / governance state | {registry} | "
        "No registry query; agent-status is a separate Foundry read |\n"
        f"| Red-team reconciliation | {redteam} | "
        "Candidate outcomes pending human sign-off; not release approval |\n"
        "| Entra sign-in logs | NOT OBSERVED IN THIS MODE | Native platform evidence only |\n"
        "| Agent 365 activity | NOT OBSERVED IN THIS MODE | Export/enablement is not ingestion |\n"
        "| Defender alerts | NOT OBSERVED IN THIS MODE | No synthetic product signals |\n"
        "| Purview audit / DLP | NOT OBSERVED IN THIS MODE | Application redaction is not DLP |\n\n"
        "Saved JSON agent status is offline evidence with unauthenticated provenance. "
        "Neither this report nor a simulated fixture certifies tenant readiness.\n"
    )
