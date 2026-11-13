"""Bounded read-only Agent 365 checks, never invented registry or governance APIs."""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, TypeAdapter

from ..azure_ops import CommandRunner, az_json
from ..config import Settings
from ..contracts import Contract

Status = Literal["PASS", "FAIL", "WARNING", "UNKNOWN", "NOT_APPLICABLE", "VERIFICATION_REQUIRED"]
SOURCE = (
    "https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent-365-data-collection"
)


class Observation(Contract):
    capability: str
    tenant: str
    agent: str
    observer: str = Field(min_length=1)
    observed_at: datetime
    evidence_url: HttpUrl
    status: Status
    notes: str = Field(min_length=10)


def prerequisites(settings: Settings) -> list[dict[str, str]]:
    return [
        {
            "check": item,
            "status": "VERIFICATION_REQUIRED",
            "reason": "Requires independent current tenant/product evidence",
        }
        for item in (
            "selected-tenant",
            "license",
            "tenant-consent",
            "admin-roles",
            "prompt-agent",
            "publishing-path",
            "registry",
            "identity-owner-sponsor",
            "activity-ingestion",
            "defender-purview",
            "cloud-support",
            "sdk-cli-availability",
        )
    ] + [
        {
            "check": "hosted-telemetry",
            "status": "NOT_APPLICABLE",
            "reason": "Selected workload is a prompt agent, not a hosted agent",
        }
    ]


def resource_status(
    settings: Settings, *, preview_api: bool = False, runner: CommandRunner = az_json
) -> dict[str, object]:
    if settings.mode == "local":
        return {
            "status": "UNKNOWN",
            "integration_status": "VERIFICATION_REQUIRED",
            "source": "LOCAL",
            "reason": "No Azure request in local mode",
        }
    if not settings.account_name or not settings.resource_group:
        raise ValueError("Foundry account and resource group required")
    # Current Learn documents these fields on a preview API; stable core never opts in silently.
    if not preview_api:
        return {
            "status": "VERIFICATION_REQUIRED",
            "integration_status": "BLOCKED_BY_PREVIEW",
            "source": SOURCE,
            "reason": "Documented fields use 2026-03-15-preview; opt in with --preview-api",
        }
    account = runner(
        [
            "resource",
            "show",
            "--resource-group",
            settings.resource_group,
            "--name",
            settings.account_name,
            "--resource-type",
            "Microsoft.CognitiveServices/accounts",
            "--subscription",
            settings.subscription_id,
            "--api-version",
            "2026-03-15-preview",
        ]
    )
    properties = TypeAdapter(dict[str, object]).validate_python(account.get("properties", {}))
    enabled = properties.get("a365LoggingEnabled")
    status = properties.get("a365Status")
    return {
        "status": "FAIL" if status == "NotLicensed" else "VERIFICATION_REQUIRED",
        "integration_status": "BLOCKED_BY_LICENSE"
        if status == "NotLicensed"
        else "READ_ONLY_VERIFICATION",
        "a365LoggingEnabled": enabled if isinstance(enabled, bool) else None,
        "a365Status": status if isinstance(status, str) else None,
        "scope": "FOUNDRY_ACCOUNT",
        "activity_ingestion": "UNKNOWN",
        "registry": "UNKNOWN",
        "source": SOURCE,
    }


def verify_observations(
    records: tuple[Observation, ...], settings: Settings, *, now: datetime | None = None
) -> dict[str, object]:
    required = {"license", "consent", "registry", "identity", "owner", "sponsor", "activity"}
    moment = now or datetime.now(UTC)
    valid: dict[str, Observation] = {}
    for record in records:
        if (
            record.tenant != settings.tenant_id
            or record.agent != settings.agent_name
            or record.observed_at.tzinfo is None
            or not moment - timedelta(hours=24) <= record.observed_at <= moment
        ):
            raise ValueError("Observation wrong scope, stale, future or missing timezone")
        if record.capability in valid:
            raise ValueError("Duplicate observation capability")
        valid[record.capability] = record
    missing = sorted(required - valid.keys())
    ok = not missing and all(valid[name].status == "PASS" for name in required)
    return {
        "status": "PASS" if ok else "VERIFICATION_REQUIRED",
        "missing": missing,
        "evidence_kind": "OPERATOR_ATTESTATION_NOT_AUTOMATED_SERVICE_VALIDATION",
        "integration_status": "OPERATOR_ATTESTATION",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("preflight", "status", "verify"))
    parser.add_argument("--preview-api", action="store_true")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--profile", choices=("equipment", "presentation"), default="equipment")
    args = parser.parse_args(argv)
    settings = Settings()
    if args.profile == "presentation":
        settings = settings.model_copy(
            update={
                "agent_name": settings.presentation_agent_name,
                "agent_version": settings.presentation_agent_version,
            }
        )
    if args.operation == "preflight":
        print(json.dumps(prerequisites(settings), indent=2))
        return 1
    if args.operation == "status":
        print(json.dumps(resource_status(settings, preview_api=args.preview_api), indent=2))
        return 1
    if args.evidence is None:
        print(json.dumps({"status": "VERIFICATION_REQUIRED", "reason": "Supply --evidence JSON"}))
        return 1
    records = TypeAdapter(tuple[Observation, ...]).validate_json(
        args.evidence.read_text(encoding="utf-8")
    )
    result = verify_observations(records, settings)
    print(json.dumps(result, indent=2))
    return int(result["status"] != "PASS")
