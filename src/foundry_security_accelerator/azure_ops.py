"""Read-only preflight and explicitly authorized infrastructure commands."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from azure.core.exceptions import AzureError
from pydantic import TypeAdapter

from .config import Settings


class CommandRunner(Protocol):
    def __call__(self, args: list[str]) -> dict[str, object]: ...


def az_json(args: list[str]) -> dict[str, object]:
    result = subprocess.run(
        ["az", *args, "--output", "json", "--only-show-errors"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode:
        # SDK/CLI error bodies may echo sensitive request data.
        raise RuntimeError(f"Azure CLI failed with exit code {result.returncode}")
    return TypeAdapter(dict[str, object]).validate_json(result.stdout)


def preflight(settings: Settings, runner: CommandRunner = az_json) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    if not shutil.which("az"):
        return [{"check": "azure-cli", "status": "FAIL", "reason": "Not installed"}]
    account = runner(["account", "show"])
    selected = (
        account.get("tenantId") == settings.tenant_id
        and account.get("id") == settings.subscription_id
        and account.get("environmentName") == settings.cloud
    )
    checks.append(
        {
            "check": "selected-account",
            "status": "PASS" if selected else "FAIL",
            "reason": "Explicit tenant/subscription/cloud match"
            if selected
            else "Configuration mismatch",
        }
    )
    for check in (
        "effective-rbac",
        "provider-registration",
        "region-foundry-support",
        "model-availability",
        "quota",
        "agent-identity",
        "monitor-ingestion",
        "government-feature-support",
    ):
        checks.append(
            {
                "check": check,
                "status": "VERIFICATION_REQUIRED",
                "reason": "Account authentication alone does not establish this capability",
            }
        )
    return checks


def whoami(settings: Settings, runner: CommandRunner = az_json) -> dict[str, str]:
    account = runner(["account", "show"])
    matched = (
        account.get("tenantId") == settings.tenant_id
        and account.get("id") == settings.subscription_id
        and account.get("environmentName") == settings.cloud
    )
    return {
        "status": "PASS" if matched else "FAIL",
        "scope": "AZURE_CLI_ACCOUNT_SELECTION_NOT_EFFECTIVE_SDK_IDENTITY",
        "identity": "REDACTED",
        "tenant": "REDACTED",
        "subscription": "REDACTED",
        "service_permissions": "VERIFICATION_REQUIRED",
    }


def infrastructure(
    settings: Settings, operation: str, *, authorized: bool = False
) -> dict[str, str]:
    if not authorized:
        return {
            "status": "NOT_EXECUTED",
            "operation": operation,
            "reason": "Supply --authorize only after reviewing scope, cost and what-if",
        }
    if not settings.resource_group or not settings.subscription_id:
        raise ValueError("Explicit resource group and subscription required")
    if operation == "cleanup":
        raise PermissionError(
            "Cleanup is manual: inspect the resource group, then authorize exact resource deletion"
        )
    if operation != "provision":
        raise ValueError("Unknown infrastructure operation")
    prechecks = preflight(settings)
    if any(check["status"] == "FAIL" for check in prechecks):
        raise PermissionError("Selected Azure account does not match explicit configuration")
    raise PermissionError(
        "Provisioning requires reviewed Bicep parameters and manual what-if; see deployment lab"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=(
            "preflight",
            "provision",
            "cleanup",
            "agent-status",
            "whoami",
            "create-agent",
            "presentation-review",
            "presentation-setup",
        ),
    )
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--profile", choices=("equipment", "presentation"), default="equipment")
    parser.add_argument("--from-json", type=Path)
    parsed = parser.parse_args(argv)
    if parsed.operation in ("presentation-review", "presentation-setup"):
        from .presentation_live import review, setup

        if parsed.operation == "presentation-setup" and not parsed.authorize:
            raise PermissionError("Presentation setup requires --authorize before settings/auth")
        settings = Settings(mode="azure")
        report = (
            review(settings)
            if parsed.operation == "presentation-review"
            else setup(settings, authorized=parsed.authorize)
        )
        print(json.dumps(report, indent=2))
        return 0
    if parsed.operation == "create-agent":
        if parsed.from_json is not None:
            parser.error("--from-json is only supported for agent-status")
        if not parsed.authorize:
            print(
                json.dumps(
                    {
                        "status": "NOT_EXECUTED",
                        "reason": "Creating a prompt-agent version requires --authorize",
                        "tools": "NONE; application-dispatched tools are not remote agent tools",
                    },
                    indent=2,
                )
            )
            return 0
        from .agent import FoundryAdapter

        print(json.dumps(FoundryAdapter(Settings(mode="azure")).deploy(authorized=True), indent=2))
        return 0
    if parsed.operation == "agent-status":
        from .agent_state import fetch_agent_status, interpret_agent_state, normalize_agent_state

        try:
            if parsed.from_json is not None:
                path = parsed.from_json
                legacy = Path("src/fsa/data/agent_state")
                if path.parent == legacy and path.name in {
                    "blocked_new_agent.json",
                    "enabled_agent.json",
                    "legacy_exception.json",
                }:
                    path = Path("data/agent_state") / path.name
                raw = TypeAdapter(dict[str, object]).validate_json(path.read_text(encoding="utf-8"))
                state = normalize_agent_state(raw)
                source = f"saved JSON {path} (offline - not a live observation)"
                label = "SIMULATED / SAVED EVIDENCE; provenance not authenticated"
            else:
                settings = Settings(mode="azure")
                if parsed.profile == "presentation":
                    settings = settings.model_copy(
                        update={
                            "agent_name": settings.presentation_agent_name,
                            "agent_version": settings.presentation_agent_version,
                        }
                    )
                state = fetch_agent_status(settings)
                source = f"Foundry project (live, read-only agents.get for '{settings.agent_name}')"
                label = "LIVE READ; not Agent 365 registry or activity verification"
        except (ImportError, ValueError, OSError, RuntimeError, AzureError) as error:
            print(
                f"Agent status unavailable ({type(error).__name__}); check packages/configuration."
            )
            return 2
        print(f"source: {source}\n{label}")
        for key, value in state.items():
            print(f"{key}: {value}")
        print("\n".join(interpret_agent_state(state)))
        return 0
    if parsed.from_json is not None:
        parser.error("--from-json is only supported for agent-status")
    settings = Settings(mode="azure") if parsed.operation == "whoami" else Settings()
    if parsed.operation == "whoami":
        identity = whoami(settings)
        print(json.dumps(identity, indent=2))
        return int(identity["status"] != "PASS")
    if parsed.operation == "preflight":
        result = preflight(settings)
        print(json.dumps(result, indent=2))
        return 0 if all(check["status"] == "PASS" for check in result) else 1
    print(
        json.dumps(
            infrastructure(settings, parsed.operation, authorized=parsed.authorize), indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
