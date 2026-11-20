"""ServiceNow as registry / system of record (AI Control Tower).

Uses the documented ServiceNow Table API:
  GET   /api/now/table/{table}?sysparm_query=u_agent_id={id}&sysparm_limit=1
  POST  /api/now/table/{table}
  PATCH /api/now/table/{table}/{sys_id}
  POST  /api/now/table/incident

The registry table defaults to the placeholder "x_ai_agent_registry".
VALIDATE: confirm the AI Control Tower table / API (and column names) with the ServiceNow team; AI Control
Tower may expose its own AI-asset inventory tables or APIs that should be used instead of a custom table.

Every write is DRY_RUN unless ``authorize=True`` and mode is azure (live).
"""

from __future__ import annotations

import base64
import urllib.parse
from typing import Any

from mccp.config import Settings
from mccp.models import AgentRecord, Receipt
from mccp.receipts import HttpError, ReceiptWriter, http_json
from mccp.registry import servicenow_payloads


class ServiceNowClient:
    def __init__(self, settings: Settings, writer: ReceiptWriter, timestamp: str = "") -> None:
        self.settings = settings
        self.writer = writer
        self.timestamp = timestamp

    # ── helpers ───────────────────────────────────────────────────────────────────────────
    def _url(self, path: str) -> str:
        base = self.settings.servicenow_instance_url or "https://contoso-health.service-now.example"
        return f"{base}{path}"

    def _headers(self) -> dict[str, str]:
        raw = f"{self.settings.servicenow_username}:{self.settings.servicenow_password}".encode()
        return {"Authorization": "Basic " + base64.b64encode(raw).decode()}

    def _live(self, authorize: bool) -> bool:
        if not authorize or self.settings.is_local:
            return False
        missing = self.settings.missing("servicenow_instance_url", "servicenow_username", "servicenow_password")
        if missing:
            raise RuntimeError(f"ServiceNow live call needs: {', '.join(missing)}")
        return True

    def _receipt(self, action: str, target: str, status: str, request: dict[str, Any], detail: dict[str, Any] | None = None) -> Receipt:
        return self.writer.write(Receipt(action=action, enforcement_point="servicenow", target=target, status=status,  # type: ignore[arg-type]
                                         mode=self.settings.mode, request=request, detail=detail or {}, timestamp=self.timestamp))

    # ── registry upsert ───────────────────────────────────────────────────────────────────
    def upsert_agents(self, agents: list[AgentRecord], authorize: bool = False) -> list[Receipt]:
        table = self.settings.servicenow_table
        receipts = []
        for row in servicenow_payloads(agents):
            query = urllib.parse.quote(f"u_agent_id={row['u_agent_id']}")
            request = {"lookup": f"GET {self._url(f'/api/now/table/{table}?sysparm_query={query}&sysparm_limit=1')}",
                       "write": f"POST|PATCH {self._url(f'/api/now/table/{table}')}", "body": row}
            if not self._live(authorize):
                receipts.append(self._receipt("registry_upsert", row["u_agent_id"], "DRY_RUN", request))
                continue
            status, _, found = http_json("GET", self._url(f"/api/now/table/{table}?sysparm_query={query}&sysparm_limit=1"), self._headers())
            if status >= 400:
                raise HttpError(status, str(found))
            results = (found or {}).get("result", [])
            if results:
                sys_id = results[0]["sys_id"]
                status, _, body = http_json("PATCH", self._url(f"/api/now/table/{table}/{sys_id}"), self._headers(), row)
            else:
                status, _, body = http_json("POST", self._url(f"/api/now/table/{table}"), self._headers(), row)
            ok = status < 300
            receipts.append(self._receipt("registry_upsert", row["u_agent_id"], "APPLIED" if ok else "FAILED", request,
                                          {"http_status": status, "sys_id": (body or {}).get("result", {}).get("sys_id", "") if ok else ""}))
        return receipts

    def set_status(self, agent_id: str, status: str, authorize: bool = False) -> Receipt:
        table = self.settings.servicenow_table
        row = {"u_status": status}
        query = urllib.parse.quote(f"u_agent_id={agent_id}")
        request = {"lookup": f"GET {self._url(f'/api/now/table/{table}?sysparm_query={query}&sysparm_limit=1')}",
                   "write": f"PATCH {self._url(f'/api/now/table/{table}/{{sys_id}}')}", "body": row}
        if not self._live(authorize):
            return self._receipt("registry_status", agent_id, "DRY_RUN", request)
        status_code, _, found = http_json("GET", self._url(f"/api/now/table/{table}?sysparm_query={query}&sysparm_limit=1"), self._headers())
        results = (found or {}).get("result", []) if status_code < 300 else []
        if not results:
            return self._receipt("registry_status", agent_id, "FAILED", request, {"http_status": status_code, "error": "CI not found"})
        status_code, _, _ = http_json("PATCH", self._url(f"/api/now/table/{table}/{results[0]['sys_id']}"), self._headers(), row)
        return self._receipt("registry_status", agent_id, "APPLIED" if status_code < 300 else "FAILED", request, {"http_status": status_code})

    # ── incident on kill ──────────────────────────────────────────────────────────────────
    def open_incident(self, agent_id: str, reason: str, authorize: bool = False, urgency: str = "1") -> Receipt:
        body = {
            "short_description": f"[AI control plane] Agent {agent_id} stopped by kill switch",
            "description": reason,
            "urgency": urgency,
            "impact": "2",
            "category": "software",
            "caller_id": "ai-control-plane",  # VALIDATE: use a real integration user sys_id
            "u_agent_id": agent_id,  # VALIDATE: custom field on incident
        }
        request = {"write": f"POST {self._url('/api/now/table/incident')}", "body": body}
        if not self._live(authorize):
            return self._receipt("incident_open", agent_id, "DRY_RUN", request)
        status, _, resp = http_json("POST", self._url("/api/now/table/incident"), self._headers(), body)
        number = (resp or {}).get("result", {}).get("number", "") if status < 300 else ""
        return self._receipt("incident_open", agent_id, "APPLIED" if status < 300 else "FAILED", request, {"http_status": status, "number": number})
