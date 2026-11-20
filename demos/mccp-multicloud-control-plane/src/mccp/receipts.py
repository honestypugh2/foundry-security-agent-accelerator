"""Receipts (JSON evidence for every mutation or dry run) and a tiny stdlib HTTP helper."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mccp.models import Receipt

_SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")
_SECRET_KEYS = {"authorization", "password", "client_secret", "client_assertion", "api-key", "ocp-apim-subscription-key", "token"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact(data: Any) -> Any:
    """Remove secrets from request/response dicts before they are written to disk."""
    if isinstance(data, dict):
        return {k: ("***REDACTED***" if k.lower() in _SECRET_KEYS else redact(v)) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data


class ReceiptWriter:
    """Writes receipts with deterministic, ordered file names."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.seq = 0
        self.receipts: list[Receipt] = []

    def write(self, receipt: Receipt) -> Receipt:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.seq += 1
        receipt.request = redact(receipt.request)
        receipt.timestamp = receipt.timestamp or utc_now_iso()
        name = _SAFE.sub("_", f"{self.seq:03d}-{receipt.action}-{receipt.enforcement_point}-{receipt.target}")[:120]
        path = self.directory / f"{name}.json"
        path.write_text(receipt.to_json() + "\n", encoding="utf-8")
        receipt.path = str(path)
        self.receipts.append(receipt)
        return receipt


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body


def http_json(method: str, url: str, headers: dict[str, str] | None = None, body: Any = None,
              form: dict[str, str] | None = None, timeout: float = 30.0) -> tuple[int, dict[str, str], Any]:
    """Minimal JSON/form HTTP client on urllib (keeps local mode free of third-party deps)."""
    hdrs = {"Accept": "application/json", **(headers or {})}
    data: bytes | None = None
    if form is not None:
        import urllib.parse

        data = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - URL comes from operator config
            raw = resp.read().decode() or "null"
            return resp.status, dict(resp.headers), _maybe_json(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        return exc.code, dict(exc.headers or {}), _maybe_json(raw)


def _maybe_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def azure_token(scope: str = "https://management.azure.com/.default") -> str:
    """Entra token via DefaultAzureCredential (azure mode only)."""
    try:
        from azure.identity import DefaultAzureCredential  # type: ignore
    except ImportError as exc:
        raise RuntimeError("azure mode needs: pip install azure-identity") from exc
    return DefaultAzureCredential().get_token(scope).token
