"""In-process approval authority. The lab approver is NOT enterprise identity proof."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from .contracts import ActionProposal, ApprovalRecord


def fingerprint(proposal: ActionProposal) -> str:
    return hashlib.sha256(proposal.model_dump_json().encode()).hexdigest()


class Approver(Protocol):
    def authorize(self, proposal: ActionProposal) -> tuple[str, bool]: ...


class LocalDemoApprover:
    def authorize(self, proposal: ActionProposal) -> tuple[str, bool]:
        return "synthetic-reviewer", True


class ApprovalService:
    def __init__(self) -> None:
        self._issued: dict[str, ApprovalRecord] = {}

    def request(
        self,
        proposal: ActionProposal,
        approver: Approver,
        *,
        now: datetime | None = None,
        ttl: timedelta = timedelta(minutes=5),
    ) -> ApprovalRecord:
        identity, approved = approver.authorize(proposal)
        if not identity or identity == proposal.subject:
            raise PermissionError("Independent approver identity required")
        if ttl <= timedelta(0):
            raise ValueError("Approval TTL must be positive")
        record = ApprovalRecord(
            approval_id=secrets.token_hex(16),
            fingerprint=fingerprint(proposal),
            approver=identity,
            scope=proposal.scope,
            approved=approved,
            expires_at=(now or datetime.now(UTC)) + ttl,
        )
        self._issued[record.approval_id] = record
        return record

    def verify(
        self, proposal: ActionProposal, record: ApprovalRecord, *, now: datetime | None = None
    ) -> None:
        if (
            self._issued.get(record.approval_id) != record
            or not record.approved
            or record.fingerprint != fingerprint(proposal)
            or record.scope != proposal.scope
            or record.expires_at <= (now or datetime.now(UTC))
        ):
            raise PermissionError("Approval missing, altered, rejected, expired or out of scope")
