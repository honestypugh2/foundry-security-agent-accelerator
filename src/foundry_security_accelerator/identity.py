"""Bind SDK credential acquisition to the explicitly selected Entra tenant."""

import base64
from typing import Protocol

from azure.core.credentials import AccessToken
from pydantic import TypeAdapter


class TokenSource(Protocol):
    def get_token(
        self,
        *scopes: str,
        claims: str | None = None,
        tenant_id: str | None = None,
        enable_cae: bool = False,
        **kwargs: object,
    ) -> AccessToken: ...


class TenantCredential:
    def __init__(self, source: TokenSource, tenant: str) -> None:
        if not tenant:
            raise ValueError("An explicit tenant is required")
        self.source = source
        self.tenant = tenant

    def get_token(
        self,
        *scopes: str,
        claims: str | None = None,
        tenant_id: str | None = None,
        enable_cae: bool = False,
        **kwargs: object,
    ) -> AccessToken:
        if tenant_id is not None and tenant_id != self.tenant:
            raise PermissionError("SDK requested a different tenant")
        token = self.source.get_token(
            *scopes, claims=claims, tenant_id=self.tenant, enable_cae=enable_cae, **kwargs
        )
        segments = token.token.split(".")
        if len(segments) != 3:
            raise PermissionError("Credential did not return a tenant-bound JWT")
        payload = base64.urlsafe_b64decode(segments[1] + "=" * (-len(segments[1]) % 4))
        # This is a scope guard on an SDK-acquired token, NOT independent JWT authentication.
        data = TypeAdapter(dict[str, object]).validate_json(payload)
        if data.get("tid") != self.tenant:
            raise PermissionError("Credential token tenant differs from selected tenant")
        return token
