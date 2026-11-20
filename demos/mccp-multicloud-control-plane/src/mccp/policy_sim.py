"""Offline emulator of infra/mccp/policies/ai-gateway.xml (SIMULATED).

The simulator processes a request in exactly the order of the XML policy so the demo,
tests and notebooks show the same decisions the real gateway makes.

    XML element (ai-gateway.xml)                        Python function
    ─────────────────────────────────────────────────── ───────────────────────────────────
    1  <validate-jwt> + <openid-config>                 PolicySimulator._validate_jwt
    2  <set-variable name="agentId|userId|cloud|costCenter">  PolicySimulator._set_variables
    3  <choose> agent_identity_mismatch → 403           PolicySimulator._check_identity_mismatch
    4  <choose> {{killswitch-global}} → 503             PolicySimulator._check_global_kill
    0  (built-in, before any policy) subscription key / state  PolicySimulator._check_subscription
    5  <choose> {{killed-agents}} → 423                 PolicySimulator._check_killed_agents
    5b <choose> {{killed-users}} → 423                  PolicySimulator._check_killed_users
    6  <llm-token-limit counter-key=agentId …>          PolicySimulator._llm_token_limit_agent
    7  <choose> {{quota-tier2-users}} + <llm-token-limit counter-key=user …>
                                                        PolicySimulator._llm_token_limit_user
    8  <llm-emit-token-metric namespace="mccp">         PolicySimulator._emit_token_metric
    9  <authentication-managed-identity> + <set-backend-service>
                                                        PolicySimulator._call_backend
   10  <outbound> <set-header …>                        PolicySimulator._outbound_headers
   11  <on-error>                                       PolicySimulator.handle (exception path)

Token-limit behaviour follows the APIM docs: tokens-per-minute exceeded → 429 with Retry-After;
token-quota exceeded → 403. VALIDATE the exact counting window (APIM may use a sliding window)
and whether the quota check is "remaining <= 0" or "remaining < estimated prompt tokens".
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

# (xml tag or marker, python function) — test_policy_sim asserts every tag exists in the XML.
XML_ELEMENT_MAP: list[tuple[str, str]] = [
    ("<validate-jwt", "_validate_jwt"),
    ("<openid-config", "_validate_jwt"),
    ('<set-variable name="agentId"', "_set_variables"),
    ('<set-variable name="userId"', "_set_variables"),
    ("agent_identity_mismatch", "_check_identity_mismatch"),
    ("{{killswitch-global}}", "_check_global_kill"),
    ("{{killed-agents}}", "_check_killed_agents"),
    ("{{killed-users}}", "_check_killed_users"),
    ('token-quota-period="Monthly"', "_llm_token_limit_agent"),
    ("{{quota-tier2-users}}", "_llm_token_limit_user"),
    ('<llm-emit-token-metric namespace="mccp"', "_emit_token_metric"),
    ("<authentication-managed-identity", "_call_backend"),
    ("<set-backend-service", "_call_backend"),
    ('<set-header name="x-user-remaining-quota-tokens"', "_outbound_headers"),
    ("<on-error>", "handle"),
]

# Local stand-in for the subscription a request authenticates with (Ocp-Apim-Subscription-Key in azure mode).
SUBSCRIPTION_HEADER = "x-sim-apim-subscription"

METRIC_DIMENSIONS = ("API ID", "agent-id", "user-id", "cloud", "cost-center")


@dataclass
class PolicyConfig:
    """Values injected into the XML by apim.bicep (defaults == main.bicep defaults)."""

    okta_issuer: str = "https://contoso-health.okta.example/oauth2/default"
    okta_audience: str = "api://contoso-ai-gateway"
    tpm_per_agent: int = 20_000
    agent_monthly_token_quota: int = 100_000_000
    # $40 / $80 per user per month at the reference blended price (finops.PriceTable.usd_to_tokens)
    user_monthly_token_quota: int = 10_500_000
    user_tier2_monthly_token_quota: int = 21_000_000
    api_id: str = "ai"
    tpm_exceeded_status: int = 429
    quota_exceeded_status: int = 403  # VALIDATE: documented status for token-quota exhaustion


@dataclass
class NamedValues:
    """APIM named values the policy reads. Updated by killswitch.py (ARM PUT in azure mode)."""

    killswitch_global: str = "false"
    killed_agents: str = "none"
    killed_users: str = "none"
    quota_tier2_users: str = "none"

    def as_dict(self) -> dict[str, str]:
        return {
            "killswitch-global": self.killswitch_global,
            "killed-agents": self.killed_agents,
            "killed-users": self.killed_users,
            "quota-tier2-users": self.quota_tier2_users,
        }

    def set(self, name: str, value: str) -> None:
        attr = name.replace("-", "_")
        if not hasattr(self, attr):
            raise KeyError(f"unknown named value {name!r}")
        setattr(self, attr, value)

    def get(self, name: str) -> str:
        return str(getattr(self, name.replace("-", "_")))


@dataclass
class GatewayRequest:
    headers: dict[str, str]
    body: dict[str, Any]
    path: str = "/ai/openai/deployments/gpt-4.1-mini/chat/completions"


@dataclass
class GatewayResponse:
    status: int
    reason: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    decided_by: str = ""
    agent_id: str = ""
    user_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def allowed(self) -> bool:
        return self.status == 200


class SimClock:
    """Deterministic clock so minute windows and month boundaries are reproducible."""

    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 11, 20, 9, 0, 0, tzinfo=timezone.utc)

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def minute_bucket(self) -> str:
        return self.now.strftime("%Y-%m-%dT%H:%M")

    def month_bucket(self) -> str:
        return self.now.strftime("%Y-%m")

    def epoch(self) -> int:
        return int(self.now.timestamp())


class _PolicyStop(Exception):
    """Internal: a <return-response> or a limit policy ended the pipeline."""

    def __init__(self, response: GatewayResponse) -> None:
        super().__init__(response.reason)
        self.response = response


def _b64url(data: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode().rstrip("=")


def _b64url_decode(part: str) -> dict[str, Any]:
    padded = part + "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode()))


def make_local_token(claims: dict[str, Any]) -> str:
    """Create an UNSIGNED, SIMULATED JWT for local mode. Never accepted by a real gateway."""
    return f"{_b64url({'alg': 'none', 'typ': 'JWT', 'kid': 'SIMULATED'})}.{_b64url(claims)}.SIMULATED"


def decode_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed JWT")
    return _b64url_decode(parts[1])


def estimate_prompt_tokens(body: dict[str, Any]) -> int:
    """Deterministic prompt-token estimate (~4 chars per token + 4 per message), like estimate-prompt-tokens."""
    messages = body.get("messages") or [{"content": body.get("input", "")}]
    return sum(4 + len(str(m.get("content", ""))) // 4 for m in messages)


def default_backend(body: dict[str, Any], prompt_tokens: int) -> tuple[dict[str, Any], int]:
    """SIMULATED Foundry model: deterministic completion sized from the prompt and max_tokens."""
    max_tokens = int(body.get("max_tokens", 256))
    completion = min(max_tokens, 32 + prompt_tokens // 2)
    payload = {
        "id": "chatcmpl-SIMULATED",
        "object": "chat.completion",
        "model": body.get("model", "gpt-4.1-mini"),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "[SIMULATED completion]"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion, "total_tokens": prompt_tokens + completion},
    }
    return payload, completion


def _in_csv(named_value: str, item: str) -> bool:
    """Same expression as the XML: ("," + list.Replace(" ","") + ",").Contains("," + item + ",")."""
    return f",{item}," in f",{named_value.replace(' ', '')},"


def _json_response(status: int, reason: str, body: dict[str, Any], decided_by: str, headers: dict[str, str] | None = None) -> GatewayResponse:
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    return GatewayResponse(status=status, reason=reason, headers=h, body=body, decided_by=decided_by)


class PolicySimulator:
    """Stateful emulator of one APIM gateway with the mccp policy applied."""

    def __init__(
        self,
        config: PolicyConfig | None = None,
        named_values: NamedValues | None = None,
        clock: SimClock | None = None,
        backend: Callable[[dict[str, Any], int], tuple[dict[str, Any], int]] = default_backend,
        on_metric: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.config = config or PolicyConfig()
        self.named_values = named_values or NamedValues()
        self.clock = clock or SimClock()
        self.backend = backend
        self.on_metric = on_metric
        self.minute_counters: dict[tuple[str, str], int] = {}
        self.quota_counters: dict[tuple[str, str], int] = {}
        self.metrics: list[dict[str, Any]] = []
        self.call_log: list[GatewayResponse] = []
        # APIM subscriptions in state "suspended" (set by killswitch ApimSubscriptionAdapter).
        self.suspended_subscriptions: set[str] = set()

    # ── public ────────────────────────────────────────────────────────────────────────────
    def handle(self, request: GatewayRequest) -> GatewayResponse:
        ctx: dict[str, Any] = {"request": request}
        try:
            self._check_subscription(ctx)
            self._validate_jwt(ctx)
            self._set_variables(ctx)
            self._check_identity_mismatch(ctx)
            self._check_global_kill(ctx)
            self._check_killed_agents(ctx)
            self._check_killed_users(ctx)
            self._llm_token_limit_agent(ctx)
            self._llm_token_limit_user(ctx)
            response = self._call_backend(ctx)
            self._emit_token_metric(ctx, response)
            self._outbound_headers(ctx, response)
        except _PolicyStop as stop:
            response = stop.response
        except Exception as exc:  # <on-error>
            response = _json_response(500, "Internal Server Error", {"error": "gateway_error", "reason": str(exc)}, "on-error")
        response.agent_id = ctx.get("agentId", "")
        response.user_id = ctx.get("userId", "")
        self.call_log.append(response)
        return response

    def quota_used(self, counter_key: str) -> int:
        return self.quota_counters.get((counter_key, self.clock.month_bucket()), 0)

    def user_quota_limit(self, user_id: str) -> int:
        if _in_csv(self.named_values.quota_tier2_users, user_id):
            return self.config.user_tier2_monthly_token_quota
        return self.config.user_monthly_token_quota

    def snapshot(self) -> dict[str, Any]:
        return {
            "named_values": self.named_values.as_dict(),
            "quota_counters": {f"{k}|{m}": v for (k, m), v in sorted(self.quota_counters.items())},
            "suspended_subscriptions": sorted(self.suspended_subscriptions),
            "now": self.clock.now.isoformat(),
        }

    def load_snapshot(self, data: dict[str, Any]) -> None:
        for name, value in data.get("named_values", {}).items():
            self.named_values.set(name, value)
        for key, value in data.get("quota_counters", {}).items():
            counter, _, month = key.rpartition("|")
            self.quota_counters[(counter, month)] = int(value)
        self.suspended_subscriptions = set(data.get("suspended_subscriptions", []))

    # ── 0 built-in subscription check (runs before the policy pipeline) ───────────────────
    def _check_subscription(self, ctx: dict[str, Any]) -> None:
        sub = ctx["request"].headers.get(SUBSCRIPTION_HEADER, "")
        if sub and sub in self.suspended_subscriptions:
            # VALIDATE: exact status/body APIM returns for a suspended subscription (documented as access denied).
            raise _PolicyStop(_json_response(
                401, "Unauthorized",
                {"error": "subscription_suspended", "message": "Access denied: subscription is not active."},
                "apim:subscription-state"))

    # ── 1 validate-jwt ────────────────────────────────────────────────────────────────────
    def _validate_jwt(self, ctx: dict[str, Any]) -> None:
        def fail(msg: str) -> None:
            raise _PolicyStop(_json_response(401, "Unauthorized", {"error": "invalid_token", "message": f"Unauthorized: invalid or missing agent token ({msg})"}, "validate-jwt"))

        auth = ctx["request"].headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            fail("missing Bearer scheme")
        try:
            claims = decode_token(auth.removeprefix("Bearer ").strip())
        except Exception:
            fail("malformed token")
            return
        aud = claims.get("aud")
        audiences = aud if isinstance(aud, list) else [aud]
        if claims.get("iss") != self.config.okta_issuer:
            fail("issuer mismatch")
        if self.config.okta_audience not in audiences:
            fail("audience mismatch")
        now = self.clock.epoch()
        if int(claims.get("exp", 0)) <= now:
            fail("token expired")
        if int(claims.get("nbf", 0)) > now:
            fail("token not yet valid")
        ctx["jwt"] = claims

    # ── 2 set-variable ────────────────────────────────────────────────────────────────────
    def _set_variables(self, ctx: dict[str, Any]) -> None:
        jwt: dict[str, Any] = ctx["jwt"]
        headers = ctx["request"].headers
        agent = jwt.get("agent_id") or headers.get("x-agent-id") or jwt.get("cid") or jwt.get("azp") or "unknown"
        ctx["agentId"] = str(agent)
        ctx["userId"] = str(jwt.get("sub", "anonymous"))
        ctx["cloud"] = headers.get("x-cloud", "unknown")
        ctx["costCenter"] = headers.get("x-cost-center", "unassigned")

    # ── 3 identity mismatch ───────────────────────────────────────────────────────────────
    def _check_identity_mismatch(self, ctx: dict[str, Any]) -> None:
        claim = str(ctx["jwt"].get("agent_id", ""))
        header = ctx["request"].headers.get("x-agent-id", "")
        if claim and header and claim != header:
            raise _PolicyStop(_json_response(403, "Forbidden", {"error": "agent_identity_mismatch", "agentId": ctx["agentId"]}, "choose:identity-mismatch"))

    # ── 4 global kill ─────────────────────────────────────────────────────────────────────
    def _check_global_kill(self, ctx: dict[str, Any]) -> None:
        if self.named_values.killswitch_global.lower() == "true":
            raise _PolicyStop(_json_response(
                503, "Service Unavailable",
                {"error": "global_kill_switch", "message": "All agent traffic is stopped by the Contoso Health AI control plane."},
                "choose:killswitch-global", {"Retry-After": "300"}))

    # ── 5 killed agents ───────────────────────────────────────────────────────────────────
    def _check_killed_agents(self, ctx: dict[str, Any]) -> None:
        if _in_csv(self.named_values.killed_agents, ctx["agentId"]):
            raise _PolicyStop(_json_response(
                423, "Locked",
                {"error": "agent_killed", "agentId": ctx["agentId"], "message": "Agent is stopped by the kill switch. Contact the agent owner."},
                "choose:killed-agents"))

    # ── 5b killed users ───────────────────────────────────────────────────────────────────
    def _check_killed_users(self, ctx: dict[str, Any]) -> None:
        if _in_csv(self.named_values.killed_users, ctx["userId"]):
            raise _PolicyStop(_json_response(
                423, "Locked",
                {"error": "user_killed", "userId": ctx["userId"], "message": "Agent access for this user is stopped by the kill switch."},
                "choose:killed-users"))

    # ── 6 llm-token-limit (agent) ─────────────────────────────────────────────────────────
    def _llm_token_limit_agent(self, ctx: dict[str, Any]) -> None:
        cfg = self.config
        key = ctx["agentId"]
        prompt = estimate_prompt_tokens(ctx["request"].body)
        ctx["promptTokens"] = prompt
        minute_key = (key, self.clock.minute_bucket())
        month_key = (key, self.clock.month_bucket())
        used_minute = self.minute_counters.get(minute_key, 0)
        used_month = self.quota_counters.get(month_key, 0)
        if used_minute + prompt > cfg.tpm_per_agent:
            retry = 60 - self.clock.now.second
            raise _PolicyStop(_json_response(
                cfg.tpm_exceeded_status, "Too Many Requests",
                {"error": "tokens_per_minute_exceeded", "agentId": key, "limit": cfg.tpm_per_agent},
                "llm-token-limit:agent-tpm",
                {"Retry-After": str(retry), "x-remaining-tokens": str(max(0, cfg.tpm_per_agent - used_minute))}))
        if used_month + prompt > cfg.agent_monthly_token_quota:
            raise _PolicyStop(_json_response(
                cfg.quota_exceeded_status, "Forbidden",
                {"error": "agent_token_quota_exceeded", "agentId": key, "quota": cfg.agent_monthly_token_quota, "period": "Monthly"},
                "llm-token-limit:agent-quota", {"x-agent-remaining-quota-tokens": "0"}))
        self.minute_counters[minute_key] = used_minute + prompt
        self.quota_counters[month_key] = used_month + prompt
        ctx["agentMinuteKey"], ctx["agentMonthKey"] = minute_key, month_key

    # ── 7 llm-token-limit (user, tier aware) ──────────────────────────────────────────────
    def _llm_token_limit_user(self, ctx: dict[str, Any]) -> None:
        user = ctx["userId"]
        tier2 = _in_csv(self.named_values.quota_tier2_users, user)
        counter = f"tier2:{user}" if tier2 else f"user:{user}"
        quota = self.config.user_tier2_monthly_token_quota if tier2 else self.config.user_monthly_token_quota
        month_key = (counter, self.clock.month_bucket())
        used = self.quota_counters.get(month_key, 0)
        prompt = ctx["promptTokens"]
        if used + prompt > quota:
            raise _PolicyStop(_json_response(
                self.config.quota_exceeded_status, "Forbidden",
                {"error": "user_token_quota_exceeded", "userId": user, "quota": quota, "period": "Monthly",
                 "message": "Monthly limit reached. Request an increase (approval workflow)."},
                "llm-token-limit:user-quota"))
        self.quota_counters[month_key] = used + prompt
        ctx["userMonthKey"], ctx["userQuota"] = month_key, quota

    # ── 9 authentication-managed-identity + set-backend-service ───────────────────────────
    def _call_backend(self, ctx: dict[str, Any]) -> GatewayResponse:
        payload, completion = self.backend(ctx["request"].body, ctx["promptTokens"])
        for key_name in ("agentMinuteKey", "agentMonthKey"):
            counters = self.minute_counters if key_name == "agentMinuteKey" else self.quota_counters
            counters[ctx[key_name]] = counters.get(ctx[key_name], 0) + completion
        self.quota_counters[ctx["userMonthKey"]] = self.quota_counters.get(ctx["userMonthKey"], 0) + completion
        ctx["completionTokens"] = completion
        return GatewayResponse(
            status=200, reason="OK", headers={"Content-Type": "application/json"}, body=payload, decided_by="backend:foundry-openai",
            prompt_tokens=ctx["promptTokens"], completion_tokens=completion)

    # ── 8 llm-emit-token-metric ───────────────────────────────────────────────────────────
    def _emit_token_metric(self, ctx: dict[str, Any], response: GatewayResponse) -> None:
        record = {
            "namespace": "mccp",
            "timestamp": self.clock.now.isoformat(),
            "dimensions": {
                "API ID": self.config.api_id,
                "agent-id": ctx["agentId"],
                "user-id": ctx["userId"],
                "cloud": ctx["cloud"],
                "cost-center": ctx["costCenter"],
            },
            "Prompt Tokens": response.prompt_tokens,
            "Completion Tokens": response.completion_tokens,
            "Total Tokens": response.prompt_tokens + response.completion_tokens,
        }
        self.metrics.append(record)
        if self.on_metric:
            self.on_metric(record)

    # ── 10 outbound ───────────────────────────────────────────────────────────────────────
    def _outbound_headers(self, ctx: dict[str, Any], response: GatewayResponse) -> None:
        cfg = self.config
        used_minute = self.minute_counters.get(ctx["agentMinuteKey"], 0)
        used_month = self.quota_counters.get(ctx["agentMonthKey"], 0)
        used_user = self.quota_counters.get(ctx["userMonthKey"], 0)
        response.headers.update({
            "x-remaining-tokens": str(max(0, cfg.tpm_per_agent - used_minute)),
            "x-agent-remaining-quota-tokens": str(max(0, cfg.agent_monthly_token_quota - used_month)),
            "x-tokens-consumed": str(response.prompt_tokens + response.completion_tokens),
            "x-user-remaining-quota-tokens": str(max(0, ctx["userQuota"] - used_user)),
            "x-agent-id": ctx["agentId"],
        })
