"""Read-only Foundry availability interpretation, independent of registry observation."""

from collections.abc import Mapping
from contextlib import ExitStack
from typing import Protocol, cast

from .config import Settings

PRINCIPLE = (
    "Runtime is enabled only if developer configuration (Foundry) "
    "AND Entra admin state both permit operation."
)
PROPAGATION = "Changes can take up to 10 minutes to reflect."


class Serializable(Protocol):
    def as_dict(self) -> dict[str, object]: ...


def _field(raw: object, snake: str, camel: str = "") -> object:
    if isinstance(raw, Mapping):
        values = cast(Mapping[str, object], raw)
        return values.get(snake, values.get(camel))
    if callable(getattr(raw, "as_dict", None)):
        return _field(cast(Serializable, raw).as_dict(), snake, camel)
    return getattr(raw, snake, getattr(raw, camel, None))


def _text(value: object) -> str:
    return (
        str(value) if isinstance(value, (str, int)) and not isinstance(value, bool) else "unknown"
    )


def normalize_agent_state(raw: object) -> dict[str, str]:
    versions = _field(raw, "versions")
    latest = _field(versions, "latest")
    return {
        "name": _text(_field(raw, "name")),
        "latest_version": _text(_field(latest, "version")),
        "state": _text(_field(raw, "state")),
        "configuration_state": _text(_field(raw, "configuration_state", "configurationState")),
        "state_source": _text(_field(raw, "state_source", "stateSource")),
        "instance_identity.status": _text(
            _field(_field(raw, "instance_identity", "instanceIdentity"), "status")
        ),
        "blueprint.status": _text(_field(_field(raw, "blueprint"), "status")),
    }


def interpret_agent_state(state: Mapping[str, str]) -> tuple[str, str, str]:
    operational = state.get("state", "unknown").lower()
    configuration = state.get("configuration_state", "unknown").lower()
    source = state.get("state_source", "unknown").lower()
    identity = state.get("instance_identity.status", "unknown").lower()
    blueprint = state.get("blueprint.status", "unknown").lower()
    blocked = identity == "disabled" or blueprint == "disabled"
    if operational == "enabled" and blocked:
        diagnosis = (
            "LEGACY EXCEPTION: runtime reports enabled despite an Entra block. Agents created "
            "before 23 Oct 2026 16:00 UTC may retain this behavior; verify creation time and "
            "disable in Foundry through an authorized operator."
        )
    elif operational == "disabled" and configuration == "disabled":
        diagnosis = (
            "Disabled by developer configuration in Foundry; Unblock in Agent 365 "
            "will not re-enable it."
        )
        if blocked or source in ("agent_instance_identity", "agent_blueprint"):
            diagnosis += " An Entra block is also reported."
    elif operational == "disabled" and source == "agent_instance_identity":
        diagnosis = (
            "Disabled by Entra admin state on the agent identity "
            "(Agent 365 Block / Disable in this tenant, or soft-delete)."
        )
    elif operational == "disabled" and source == "agent_blueprint":
        diagnosis = "Disabled by Entra admin state on the agent blueprint; affects agents from it."
    elif operational == "disabled":
        diagnosis = (
            "Disabled, but neither state_source nor configuration_state explains why; "
            "check the Foundry portal."
        )
    elif (
        operational == "enabled"
        and configuration == "enabled"
        and identity == blueprint == "active"
    ):
        diagnosis = "Enabled: developer configuration and Entra admin state both permit operation."
    elif operational == "enabled":
        diagnosis = (
            "Enabled is reported, but not all states permit operation or are reported; "
            "not confirmed fully enabled."
        )
    else:
        diagnosis = "Operational state not recognised; confirm in the Foundry portal."
    return PRINCIPLE, diagnosis, PROPAGATION


def fetch_agent_status(settings: Settings) -> dict[str, str]:
    if settings.mode != "azure":
        raise ValueError("Live agent-status requires Azure mode")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    from .identity import TenantCredential

    with ExitStack() as stack:
        credential = stack.enter_context(DefaultAzureCredential(authority=settings.authority))
        project = stack.enter_context(
            AIProjectClient(
                endpoint=settings.project_endpoint,
                credential=TenantCredential(credential, settings.tenant_id),
                credential_scopes=[settings.project_scope],
                retry_total=0,
                connection_timeout=15,
                read_timeout=30,
                logging_enable=False,
            )
        )
        return normalize_agent_state(project.agents.get(agent_name=settings.agent_name))
