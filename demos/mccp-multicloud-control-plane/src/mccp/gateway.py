"""Client for the APIM AI gateway (OpenAI-compatible chat completions).

Local mode routes requests to PolicySimulator; azure mode POSTs to APIM_GATEWAY_URL.
Every call carries x-agent-id, x-cloud, x-cost-center and an Okta (or Entra) bearer token.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mccp.config import Settings
from mccp.models import AgentRecord
from mccp.policy_sim import SUBSCRIPTION_HEADER, GatewayRequest, PolicySimulator
from mccp.receipts import http_json

OUTCOMES: dict[int, str] = {
    200: "allowed",
    401: "unauthenticated",
    403: "forbidden_or_quota",
    423: "killed",
    429: "throttled",
    503: "global_kill",
}


@dataclass
class CallResult:
    status: int
    outcome: str
    agent_id: str
    user_id: str
    remaining_tokens: int | None = None
    agent_remaining_quota: int | None = None
    user_remaining_quota: int | None = None
    tokens_consumed: int | None = None
    retry_after: int | None = None
    error: str = ""
    decided_by: str = ""
    body: dict[str, Any] = field(default_factory=dict)
    simulated: bool = True


def _int(headers: dict[str, str], name: str) -> int | None:
    lower = {k.lower(): v for k, v in headers.items()}
    value = lower.get(name.lower())
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


def parse_response(status: int, headers: dict[str, str], body: Any, agent_id: str, user_id: str, simulated: bool, decided_by: str = "") -> CallResult:
    body = body if isinstance(body, dict) else {"raw": body}
    err = body.get("error", "")
    if isinstance(err, dict):  # OpenAI-style {"error": {"code": ...}}
        err = err.get("code") or err.get("message", "")
    return CallResult(
        status=status,
        outcome=OUTCOMES.get(status, "error"),
        agent_id=agent_id,
        user_id=user_id,
        remaining_tokens=_int(headers, "x-remaining-tokens"),
        agent_remaining_quota=_int(headers, "x-agent-remaining-quota-tokens"),
        user_remaining_quota=_int(headers, "x-user-remaining-quota-tokens"),
        tokens_consumed=_int(headers, "x-tokens-consumed"),
        retry_after=_int(headers, "Retry-After"),
        error=str(err),
        decided_by=decided_by,
        body=body,
        simulated=simulated,
    )


def azure_chat_body(prompt: str, max_tokens: int, reasoning_effort: str = "minimal") -> dict[str, Any]:
    """Request body for the live gateway. gpt-5 family (reasoning) models reject max_tokens and take
    max_completion_tokens; reasoning tokens count against it, so keep reasoning_effort low for short answers."""
    body: dict[str, Any] = {"messages": [{"role": "user", "content": prompt}], "max_completion_tokens": max_tokens}
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    return body


def gateway_token(settings: Settings, explicit: str = "") -> str:
    """Bearer token for the live gateway: --token wins; else Entra (az login / managed identity) or Okta,
    matching the identityProvider the gateway was deployed with."""
    if explicit:
        return explicit
    if settings.identity_provider == "okta":
        from mccp.okta import OktaClient
        return OktaClient(settings).client_credentials_token()["access_token"]
    from mccp.receipts import azure_token
    return azure_token("https://cognitiveservices.azure.com/.default")


class GatewayClient:
    def __init__(self, settings: Settings, simulator: PolicySimulator | None = None) -> None:
        self.settings = settings
        self.simulator = simulator

    def headers_for(self, agent: AgentRecord, token: str) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {token}",
            "x-agent-id": agent.agent_id,
            "x-cloud": agent.cloud,
            "x-cost-center": agent.cost_center,
        }
        if self.settings.apim_subscription_key:
            h["Ocp-Apim-Subscription-Key"] = self.settings.apim_subscription_key
        return h

    def chat(self, agent: AgentRecord, token: str, prompt: str, user_id: str = "", max_tokens: int = 256,
             header_overrides: dict[str, str] | None = None) -> CallResult:
        deployment = self.settings.foundry_model_deployment
        body = {"model": deployment, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
        if not self.settings.is_local:
            body = azure_chat_body(prompt, max_tokens, self.settings.reasoning_effort)
        headers = {**self.headers_for(agent, token), **(header_overrides or {})}
        if self.settings.is_local:
            if self.simulator is None:
                raise RuntimeError("local mode needs a PolicySimulator")
            if agent.apim_subscription_id:
                headers.setdefault(SUBSCRIPTION_HEADER, agent.apim_subscription_id)
            resp = self.simulator.handle(GatewayRequest(headers=headers, body=body))
            return parse_response(resp.status, resp.headers, resp.body, resp.agent_id or agent.agent_id, resp.user_id or user_id, True, resp.decided_by)
        if not self.settings.apim_gateway_url:
            raise RuntimeError("APIM_GATEWAY_URL is not set")
        # Path matches infra/mccp/modules/apim.bicep: API path "ai/openai" + operation /deployments/{id}/chat/completions.
        url = (f"{self.settings.apim_gateway_url}/{self.settings.apim_api_path}/openai/deployments/{deployment}"
               f"/chat/completions?api-version={self.settings.foundry_openai_api_version}")
        status, resp_headers, resp_body = http_json("POST", url, headers, body, timeout=60)
        return parse_response(status, resp_headers, resp_body, agent.agent_id, user_id, False, "apim")
