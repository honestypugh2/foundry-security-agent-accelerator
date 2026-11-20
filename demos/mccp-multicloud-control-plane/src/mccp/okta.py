"""Okta as agent identity: one Okta API Services (service) app per agent.

Runtime:  client-credentials grant with private_key_jwt client authentication against a custom
          authorization server ({OKTA_ISSUER}/v1/token). Tokens carry aud = OKTA_AUDIENCE and are
          validated by APIM <validate-jwt> with the issuer's openid-config.
Kill:     POST {OKTA_ORG_URL}/api/v1/apps/{appId}/lifecycle/deactivate  (revive: .../activate)
          Deactivation stops NEW tokens. Access tokens already issued stay valid until "exp" because APIM
          validates them locally — keep agent token lifetime short (e.g. 5-15 min) and rely on the gateway
          kill list for immediate effect. VALIDATE token lifetime policy on the authorization server.

VALIDATE: Okta's dedicated AI-agent identity features (e.g. "Okta for AI Agents") may replace the
one-service-app-per-agent pattern; the lifecycle endpoints used here are the documented Apps API.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from mccp.config import Settings
from mccp.models import AgentRecord, Receipt
from mccp.policy_sim import SimClock, decode_token, make_local_token
from mccp.receipts import ReceiptWriter, http_json

try:  # optional extra "okta" = pyjwt[crypto]
    import jwt as pyjwt  # type: ignore
except ImportError:  # pragma: no cover
    pyjwt = None  # type: ignore[assignment]

CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"


def local_agent_token(agent: AgentRecord, user_id: str, clock: SimClock, issuer: str, audience: str,
                      ttl_seconds: int = 900, **extra_claims: Any) -> str:
    """SIMULATED Okta access token for local mode (unsigned; never valid against a real gateway)."""
    now = clock.epoch()
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": user_id,
        "cid": agent.okta_app_id,
        "agent_id": agent.agent_id,
        "scp": ["ai.gateway.invoke"],
        "iat": now,
        "nbf": now,
        "exp": now + ttl_seconds,
        "jti": f"SIM-{agent.agent_id}-{now}",
    }
    claims.update(extra_claims)
    return make_local_token(claims)


def build_client_assertion(client_id: str, token_url: str, private_key_pem: str, key_id: str = "") -> str:
    """private_key_jwt client assertion (RFC 7523) signed RS256 with the service app's private key."""
    if pyjwt is None:
        raise RuntimeError("pip install 'pyjwt[crypto]'  (optional extra 'okta')")
    now = int(time.time())
    payload = {"iss": client_id, "sub": client_id, "aud": token_url, "iat": now, "exp": now + 300, "jti": str(uuid.uuid4())}
    headers = {"kid": key_id} if key_id else None
    return pyjwt.encode(payload, private_key_pem, algorithm="RS256", headers=headers)


class OktaClient:
    def __init__(self, settings: Settings, writer: ReceiptWriter | None = None, timestamp: str = "") -> None:
        self.settings = settings
        self.writer = writer
        self.timestamp = timestamp

    # ── runtime token (live) ──────────────────────────────────────────────────────────────
    def client_credentials_token(self, client_id: str = "", private_key_path: str = "", key_id: str = "") -> dict[str, Any]:
        s = self.settings
        client_id = client_id or s.okta_client_id
        key_path = private_key_path or s.okta_private_key_path
        missing = [n for n, v in (("OKTA_ISSUER", s.okta_issuer), ("OKTA_CLIENT_ID", client_id), ("OKTA_PRIVATE_KEY_PATH", key_path)) if not v]
        if missing:
            raise RuntimeError(f"Okta token needs: {', '.join(missing)}")
        token_url = f"{s.okta_issuer}/v1/token"
        assertion = build_client_assertion(client_id, token_url, Path(key_path).read_text(encoding="utf-8"), key_id or s.okta_key_id)
        status, _, body = http_json("POST", token_url, form={
            "grant_type": "client_credentials",
            "scope": s.okta_scopes,
            "client_assertion_type": CLIENT_ASSERTION_TYPE,
            "client_assertion": assertion,
        })
        if status >= 400:
            raise RuntimeError(f"Okta token request failed: HTTP {status} {body}")
        return body

    def introspect(self, token: str, client_id: str = "", private_key_path: str = "") -> dict[str, Any]:
        """Live: POST {issuer}/v1/introspect. Local: decode the SIMULATED token and report its claims."""
        if self.settings.is_local:
            claims = decode_token(token)
            return {"active": True, "source": "SIMULATED", **claims}
        s = self.settings
        url = f"{s.okta_issuer}/v1/introspect"
        client_id = client_id or s.okta_client_id
        assertion = build_client_assertion(client_id, url, Path(private_key_path or s.okta_private_key_path).read_text(encoding="utf-8"), s.okta_key_id)
        status, _, body = http_json("POST", url, form={
            "token": token, "token_type_hint": "access_token", "client_id": client_id,
            "client_assertion_type": CLIENT_ASSERTION_TYPE, "client_assertion": assertion,
        })
        if status >= 400:
            raise RuntimeError(f"Okta introspection failed: HTTP {status} {body}")
        return body

    # ── lifecycle (identity kill switch) ──────────────────────────────────────────────────
    def set_app_lifecycle(self, agent: AgentRecord, activate: bool, authorize: bool = False) -> Receipt:
        action = "activate" if activate else "deactivate"
        org = self.settings.okta_org_url or "https://contoso-health.okta.example"
        url = f"{org}/api/v1/apps/{agent.okta_app_id}/lifecycle/{action}"
        request = {"method": "POST", "url": url, "headers": {"Authorization": "SSWS ***"}}
        if not agent.okta_app_id:
            return self._write(Receipt(action=f"identity_{action}", enforcement_point="okta", target=agent.agent_id, status="SKIPPED",
                                       mode=self.settings.mode, request=request, detail={"reason": "no okta_app_id"}, timestamp=self.timestamp))
        if not authorize or self.settings.is_local:
            return self._write(Receipt(action=f"identity_{action}", enforcement_point="okta", target=agent.agent_id, status="DRY_RUN",
                                       mode=self.settings.mode, request=request, timestamp=self.timestamp,
                                       detail={"note": "Deactivation blocks new tokens; existing tokens expire per their exp."}))
        if not self.settings.okta_org_url or not self.settings.okta_api_token:
            raise RuntimeError("Okta lifecycle needs OKTA_ORG_URL and OKTA_API_TOKEN (or an OAuth token with okta.apps.manage)")
        status, _, body = http_json("POST", url, {"Authorization": f"SSWS {self.settings.okta_api_token}"})
        return self._write(Receipt(action=f"identity_{action}", enforcement_point="okta", target=agent.agent_id,
                                   status="APPLIED" if status < 300 else "FAILED", mode=self.settings.mode, request=request,
                                   detail={"http_status": status, "response": body if status >= 300 else ""}, timestamp=self.timestamp))

    def _write(self, receipt: Receipt) -> Receipt:
        return self.writer.write(receipt) if self.writer else receipt
