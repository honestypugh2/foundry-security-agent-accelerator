"""Kill switch: stop (or revive) an agent, a user, or the whole platform across every enforcement point.

Scopes:  agent  ·  user  ·  global (platform)
Order:   gateway first (fast, stops traffic in seconds) → identity second (no new tokens) → record third.

  #  Enforcement point                 agent  user  global  How
  1  APIM named values                   ✔     ✔      ✔     ARM PUT namedValues/{killed-agents|killed-users|killswitch-global}
  2  APIM subscription suspend          opt    –      –     ARM PATCH subscriptions/{sid} state=suspended  (--hard)
  3  Okta app lifecycle                  ✔     –      –     POST /api/v1/apps/{id}/lifecycle/deactivate|activate
  4  ServiceNow                          ✔     ✔      ✔     CI u_status=killed|active + incident (kill only)
  5  Platform-native (Foundry, Entra Agent ID, Copilot Studio, Snowflake)   MANUAL instructions only (no fake API)
  6  AWS IAM deny policy (optional extra)  ✔     –      –     iam.put_role_policy / delete_role_policy on the agent role

Every mutation requires authorize=True. Without it each point writes a DRY_RUN receipt.
In local mode, points 1–2 change the in-process PolicySimulator (status SIMULATED) when authorized;
external systems (3, 4, 6) are always DRY_RUN in local mode.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from mccp.config import Settings
from mccp.models import AgentRecord, KillOrder, Receipt
from mccp.okta import OktaClient
from mccp.policy_sim import PolicySimulator
from mccp.receipts import ReceiptWriter, azure_token, http_json
from mccp.servicenow import ServiceNowClient

ARM = "https://management.azure.com"
NAMED_VALUE_BY_SCOPE = {"agent": "killed-agents", "user": "killed-users", "global": "killswitch-global"}
EMPTY_LIST_SENTINEL = "none"  # APIM named values "may not be empty" (ARM reference)


def csv_add(current: str, item: str) -> str:
    items = [i for i in current.replace(" ", "").split(",") if i and i != EMPTY_LIST_SENTINEL]
    if item not in items:
        items.append(item)
    return ",".join(items) or EMPTY_LIST_SENTINEL


def csv_remove(current: str, item: str) -> str:
    items = [i for i in current.replace(" ", "").split(",") if i and i not in (EMPTY_LIST_SENTINEL, item)]
    return ",".join(items) or EMPTY_LIST_SENTINEL


def named_value_request(settings: Settings, name: str, value: str) -> dict[str, Any]:
    return {
        "method": "PUT",
        "url": f"{ARM}{settings.apim_resource_id or '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ApiManagement/service/<apim>'}"
               f"/namedValues/{name}?api-version={settings.apim_api_version}",
        "body": {"properties": {"displayName": name, "value": value, "secret": False}},
    }


def read_named_value(settings: Settings, name: str, token: str) -> tuple[int, str]:
    """Current value of an APIM named value. A GET does not return the value (ARM reference: "This property will
    not be filled on 'GET' operations"), so read it with POST .../namedValues/{name}/listValue -> {"value": "..."}."""
    url = (f"{ARM}{settings.apim_resource_id}/namedValues/{name}/listValue"
           f"?api-version={settings.apim_api_version}")
    status, _, body = http_json("POST", url, {"Authorization": f"Bearer {token}"})
    value = body.get("value", EMPTY_LIST_SENTINEL) if isinstance(body, dict) else EMPTY_LIST_SENTINEL
    return status, str(value or EMPTY_LIST_SENTINEL)


def subscription_request(settings: Settings, sid: str, state: str) -> dict[str, Any]:
    return {
        "method": "PATCH",
        "url": f"{ARM}{settings.apim_resource_id or '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ApiManagement/service/<apim>'}"
               f"/subscriptions/{sid}?api-version={settings.apim_api_version}",
        "headers": {"If-Match": "*"},
        "body": {"properties": {"state": state}},
    }


@dataclass
class Context:
    settings: Settings
    writer: ReceiptWriter
    authorize: bool
    simulator: PolicySimulator | None = None
    timestamp: str = ""
    hard: bool = False

    def receipt(self, **kw: Any) -> Receipt:
        return self.writer.write(Receipt(mode=self.settings.mode, timestamp=self.timestamp, **kw))


class EnforcementPoint(Protocol):
    name: str

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]: ...


class ApimNamedValueAdapter:
    name = "apim-named-value"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        nv = NAMED_VALUE_BY_SCOPE[order.scope]
        action = "revive" if order.revive else "kill"
        current = self._read(nv, ctx)
        if order.scope == "global":
            new_value = "false" if order.revive else "true"
        else:
            new_value = csv_remove(current or EMPTY_LIST_SENTINEL, order.target) if order.revive else csv_add(current or EMPTY_LIST_SENTINEL, order.target)
        req = named_value_request(ctx.settings, nv, new_value)
        detail = {"named_value": nv, "previous": current if current is not None else "(read at apply time)", "new": new_value}
        if not ctx.authorize:
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="DRY_RUN", request=req, detail=detail)]
        if ctx.settings.is_local:
            assert ctx.simulator is not None
            ctx.simulator.named_values.set(nv, new_value)
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="SIMULATED", request=req, detail=detail)]
        token = azure_token()
        status, _, body = http_json("PUT", req["url"], {"Authorization": f"Bearer {token}"}, req["body"])
        detail.update(http_status=status, note="202 = accepted; gateway picks up the new value shortly (VALIDATE propagation time)")
        return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target,
                            status="APPLIED" if status < 300 else "FAILED", request=req, detail={**detail, "response": body if status >= 300 else ""})]

    @staticmethod
    def _read(name: str, ctx: Context) -> str | None:
        if ctx.settings.is_local:
            return ctx.simulator.named_values.get(name) if ctx.simulator else None
        if not ctx.authorize or not ctx.settings.apim_resource_id:
            return None
        status, value = read_named_value(ctx.settings, name, azure_token())
        if status >= 300:
            raise RuntimeError(f"cannot read named value {name}: HTTP {status}")
        return value


class ApimSubscriptionAdapter:
    """Hard stop: suspends the agent's APIM subscription (requests fail before any policy runs)."""

    name = "apim-subscription"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        action = "revive" if order.revive else "kill"
        if order.scope != "agent" or agent is None or not agent.apim_subscription_id:
            return []
        if not ctx.hard and not order.revive:
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="SKIPPED",
                                detail={"reason": "soft kill: named value returns a clear 423; use --hard to also suspend the subscription"})]
        state = "active" if order.revive else "suspended"
        req = subscription_request(ctx.settings, agent.apim_subscription_id, state)
        if not ctx.authorize:
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="DRY_RUN", request=req)]
        if ctx.settings.is_local:
            assert ctx.simulator is not None
            if order.revive:
                ctx.simulator.suspended_subscriptions.discard(agent.apim_subscription_id)
            else:
                ctx.simulator.suspended_subscriptions.add(agent.apim_subscription_id)
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="SIMULATED", request=req)]
        token = azure_token()
        status, _, body = http_json("PATCH", req["url"], {"Authorization": f"Bearer {token}", "If-Match": "*"}, req["body"])
        return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="APPLIED" if status < 300 else "FAILED",
                            request=req, detail={"http_status": status, "response": body if status >= 300 else ""})]


class OktaAdapter:
    name = "okta"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        if order.scope != "agent" or agent is None:
            return [ctx.receipt(action="revive" if order.revive else "kill", enforcement_point=self.name, target=order.target, status="SKIPPED",
                                detail={"reason": f"{order.scope} scope is enforced at the gateway; agent identities stay active"})]
        return [OktaClient(ctx.settings, ctx.writer, ctx.timestamp).set_app_lifecycle(agent, activate=order.revive, authorize=ctx.authorize)]


class ServiceNowAdapter:
    name = "servicenow"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        client = ServiceNowClient(ctx.settings, ctx.writer, ctx.timestamp)
        out = []
        if order.scope == "agent":
            out.append(client.set_status(order.target, "active" if order.revive else "killed", authorize=ctx.authorize))
        if not order.revive:
            out.append(client.open_incident(order.target, f"{order.scope} kill: {order.reason} (requested by {order.requested_by})",
                                            authorize=ctx.authorize))
        return out


PLATFORM_INSTRUCTIONS = {
    "foundry": [
        "Microsoft 365 admin center (Agent 365) → Agents → select agent → Block (Foundry definition and Azure resources are kept; can take up to 10 minutes). Alternative for Foundry-hosted usage: Foundry → Manage → Cost → cost control with action Block usage (preview).",
        "Entra admin center → Agent ID (agent identities) → disable the agent identity {entra}.  VALIDATE availability in tenant.",
    ],
    "copilot_studio": [
        "Power Platform admin center → quarantine / disable the Copilot Studio agent, or unpublish it in Copilot Studio.  VALIDATE.",
        "Entra admin center → disable the agent identity {entra} if one is assigned.",
    ],
    "snowflake_cortex": [
        "Snowflake: REVOKE ROLE <agent_role> FROM USER <agent_service_user>; (stops Cortex calls made with that role).",
    ],
    "servicenow": ["ServiceNow AI Control Tower: deactivate the agent in the AI asset inventory.  VALIDATE."],
    "bedrock": ["AWS console: optional — disassociate the agent alias; IAM deny policy below already blocks invocations."],
    "agentcore": ["AWS console: optional — stop / delete the AgentCore runtime endpoint; IAM deny policy below blocks model calls."],
}


class PlatformManualAdapter:
    """Prints admin steps for platforms without a supported programmatic stop. Never calls a made-up API."""

    name = "platform-native"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        if order.scope != "agent" or agent is None:
            return []
        steps = [s.format(entra=agent.entra_agent_id or "(none)") for s in PLATFORM_INSTRUCTIONS.get(agent.platform, [])]
        if order.revive:
            steps = [f"Reverse: {s}" for s in steps]
        if not agent.gateway_routed:
            steps.insert(0, "Agent does NOT route through the APIM gateway: platform-native stop + Okta are the effective controls.")
        return [ctx.receipt(action="revive" if order.revive else "kill", enforcement_point=self.name, target=order.target, status="MANUAL",
                            detail={"platform": agent.platform, "steps": steps})]


DENY_POLICY_NAME = "mccp-killswitch-deny"
DENY_POLICY = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "MccpKillSwitch",
        "Effect": "Deny",
        "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream", "bedrock:Converse", "bedrock:ConverseStream",
                   "bedrock:InvokeAgent", "bedrock-agentcore:*"],
        "Resource": "*",
    }],
}


class AwsIamDenyAdapter:
    name = "aws-iam"

    def apply(self, order: KillOrder, agent: AgentRecord | None, ctx: Context) -> list[Receipt]:
        if order.scope != "agent" or agent is None or agent.cloud != "aws" or not agent.aws_role_name:
            return []
        action = "revive" if order.revive else "kill"
        req = ({"api": "iam.delete_role_policy", "RoleName": agent.aws_role_name, "PolicyName": DENY_POLICY_NAME} if order.revive else
               {"api": "iam.put_role_policy", "RoleName": agent.aws_role_name, "PolicyName": DENY_POLICY_NAME, "PolicyDocument": DENY_POLICY})
        if not ctx.authorize or ctx.settings.is_local:
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="DRY_RUN", request=req)]
        try:
            import boto3  # type: ignore
        except ImportError:
            return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="SKIPPED", request=req,
                                detail={"reason": "pip install boto3 (optional extra 'aws')"})]
        iam = boto3.client("iam")
        if order.revive:
            iam.delete_role_policy(RoleName=agent.aws_role_name, PolicyName=DENY_POLICY_NAME)
        else:
            iam.put_role_policy(RoleName=agent.aws_role_name, PolicyName=DENY_POLICY_NAME, PolicyDocument=json.dumps(DENY_POLICY))
        return [ctx.receipt(action=action, enforcement_point=self.name, target=order.target, status="APPLIED", request=req)]


DEFAULT_POINTS: list[EnforcementPoint] = [
    ApimNamedValueAdapter(),     # gateway (fast)
    ApimSubscriptionAdapter(),   # gateway hard stop (optional)
    OktaAdapter(),               # identity
    AwsIamDenyAdapter(),         # cloud identity (AWS)
    ServiceNowAdapter(),         # record
    PlatformManualAdapter(),     # platform-native admin steps
]


class KillSwitch:
    def __init__(self, settings: Settings, writer: ReceiptWriter, simulator: PolicySimulator | None = None,
                 points: list[EnforcementPoint] | None = None) -> None:
        self.settings = settings
        self.writer = writer
        self.simulator = simulator
        self.points = points if points is not None else DEFAULT_POINTS

    def execute(self, order: KillOrder, agents: list[AgentRecord], authorize: bool = False, timestamp: str = "",
                hard: bool = False) -> list[Receipt]:
        if order.scope not in NAMED_VALUE_BY_SCOPE:
            raise ValueError(f"unknown scope {order.scope!r}")
        agent = next((a for a in agents if a.agent_id == order.target), None) if order.scope == "agent" else None
        if order.scope == "agent" and agent is None:
            raise KeyError(f"agent {order.target!r} not in inventory")
        ctx = Context(self.settings, self.writer, authorize, self.simulator, timestamp, hard)
        receipts: list[Receipt] = []
        for point in self.points:
            try:
                receipts.extend(point.apply(order, agent, ctx))
            except RuntimeError as exc:  # e.g. Okta/ServiceNow not configured: record it and keep going
                receipts.append(ctx.receipt(action="revive" if order.revive else "kill",
                                            enforcement_point=getattr(point, "name", type(point).__name__),
                                            target=order.target, status="SKIPPED", detail={"reason": str(exc)}))
        if agent is not None and authorize:
            agent.status = "active" if order.revive else "killed"
        return receipts


def approve_quota_increase(settings: Settings, writer: ReceiptWriter, user_id: str, authorize: bool, approver: str,
                           simulator: PolicySimulator | None = None, timestamp: str = "") -> Receipt:
    """Approval for more: add the user to {{quota-tier2-users}} (larger monthly counter in the policy)."""
    name = "quota-tier2-users"
    current = simulator.named_values.get(name) if (settings.is_local and simulator) else None
    new_value = csv_add(current or EMPTY_LIST_SENTINEL, user_id)
    req = named_value_request(settings, name, new_value)
    detail = {"approver": approver, "named_value": name, "previous": current if current is not None else "(read at apply time)", "new": new_value}
    base = dict(action="approve_increase", enforcement_point="apim-named-value", target=user_id, mode=settings.mode, request=req, timestamp=timestamp)
    if not authorize:
        return writer.write(Receipt(status="DRY_RUN", detail=detail, **base))  # type: ignore[arg-type]
    if settings.is_local:
        assert simulator is not None
        simulator.named_values.set(name, new_value)
        return writer.write(Receipt(status="SIMULATED", detail=detail, **base))  # type: ignore[arg-type]
    token = azure_token()
    status, current_value = read_named_value(settings, name, token)
    if status < 300:
        req = named_value_request(settings, name, csv_add(current_value, user_id))
        base["request"] = req
    status, _, body = http_json("PUT", req["url"], {"Authorization": f"Bearer {token}"}, req["body"])
    return writer.write(Receipt(status="APPLIED" if status < 300 else "FAILED", detail={**detail, "http_status": status}, **base))  # type: ignore[arg-type]
