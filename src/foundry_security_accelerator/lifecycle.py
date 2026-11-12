"""Bounded local lifecycle evidence, with no platform clients or business action sink."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from .audit import AuditLog, verify_audit
from .contracts import ApprovalRecord

_KIND = "LOCAL_SIMULATION_NOT_AGENT365_OR_ENTRA"
_ADMIN = "ai-admin"
_RESOURCES = ("synthetic-regulated-records", "synthetic-internal-documents")


def _response(**values: object) -> dict[str, object]:
    return {"kind": _KIND, "platform_actions": "NOT_EXECUTED", **values}


@dataclass(frozen=True)
class _Proposal:
    version: int
    requester: str = "maker"
    owner: str = "synthetic-owner"
    sponsor: str = "synthetic-sponsor"
    agent_identity: str = "synthetic-agent-identity"
    release_gate_passed: bool = True
    write_approval_required: bool = True
    open_outbound: bool = False
    clearance: str = "Internal"
    package_resources: tuple[str, ...] = _RESOURCES
    package_duration_days: int = 180
    template: str = "synthetic-regulated-data-agents"
    tools: tuple[str, ...] = ("synthetic-records-reader",)
    resources: tuple[str, ...] = _RESOURCES
    mode: str = "READ_ONLY"
    attributes: tuple[str, ...] = ("classification:synthetic-regulated", "owner:synthetic")
    conditional_access: str = "DESCRIPTIVE_ONLY: require strong authentication"
    access_package: str = "DESCRIPTIVE_ONLY: time-bounded least-privilege access"


def _fingerprint(proposal: _Proposal) -> str:
    return hashlib.sha256(
        json.dumps(asdict(proposal), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class _Lifecycle:
    """Local authority only; equipment-specific ApprovalService cannot bind this schema."""

    def __init__(self, path: Path, run_id: str) -> None:
        self.audit = AuditLog(path / "audit.jsonl", run_id)
        self.audit_head = ""
        self.current_version = 0
        self._pending: _Proposal | None = None
        self._reviewed: str | None = None
        self._issued: dict[str, ApprovalRecord] = {}
        self._published: _Proposal | None = None
        self._authorization: ApprovalRecord | None = None
        self.package_expires_at: datetime | None = None

    def _record(self, event: str, **data: str) -> None:
        receipt = self.audit.append(
            event, {"kind": _KIND, "platform_actions": "NOT_EXECUTED", **data}
        )
        self.audit_head = receipt.hash

    def _deny(self, reason: str) -> None:
        self._record("transition_denied", reason=reason)
        raise PermissionError(f"{_KIND}: {reason}; platform_actions=NOT_EXECUTED")

    def _check_pending(self, proposal: _Proposal) -> None:
        if self._pending != proposal or proposal.version != self.current_version + 1:
            self._deny("Proposal is changed, stale, or not requested")

    def request(self, proposal: _Proposal) -> dict[str, object]:
        if self._pending is not None or proposal.version != self.current_version + 1:
            self._deny("Only the next version may be requested once")
        self._pending = proposal
        self._reviewed = None
        self._record("requested", fingerprint=_fingerprint(proposal), version=str(proposal.version))
        return _response(status="REQUESTED", version=proposal.version)

    def review(self, proposal: _Proposal) -> dict[str, object]:
        self._check_pending(proposal)
        findings: list[str] = []
        requirements = (
            (
                "REQ01",
                "Owner and sponsor",
                bool(proposal.owner.strip() and proposal.sponsor.strip()),
            ),
            (
                "REQ02",
                "Own agent identity",
                proposal.agent_identity.startswith("synthetic-agent-")
                and proposal.agent_identity != proposal.requester,
            ),
            ("REQ03", "Release gate", proposal.release_gate_passed),
            ("REQ04", "Write approval", proposal.write_approval_required),
            ("REQ05", "No open outbound", not proposal.open_outbound),
            (
                "REQ06",
                "Clearance capped at Internal",
                proposal.clearance in {"Public", "Internal"},
            ),
            (
                "REQ07",
                "Grants within access package",
                bool(proposal.resources)
                and set(proposal.resources) <= set(proposal.package_resources)
                and set(proposal.package_resources) <= set(_RESOURCES)
                and 0 < proposal.package_duration_days <= 180,
            ),
        )
        for requirement, name, passed in requirements:
            if not passed:
                findings.append(f"{requirement}: {name}")
        if proposal.template != "synthetic-regulated-data-agents":
            findings.append("Unrecognized local policy template")
        if proposal.mode != "READ_ONLY":
            findings.append("Only READ_ONLY local access is permitted")
        if proposal.tools != ("synthetic-records-reader",):
            findings.append("Tools must match the exact synthetic read-only allowlist")
        if not set(proposal.resources) <= set(_RESOURCES):
            findings.append("Resources must match the exact synthetic allowlist")
        if set(proposal.attributes) != {
            "classification:synthetic-regulated",
            "owner:synthetic",
        }:
            findings.append("Required descriptive classification and owner attributes are missing")
        if (
            proposal.conditional_access != _Proposal(1).conditional_access
            or proposal.access_package != _Proposal(1).access_package
        ):
            findings.append("Conditional access and access package must remain descriptive only")
        self._reviewed = None if findings else _fingerprint(proposal)
        self._record(
            "review_failed" if findings else "review_passed",
            fingerprint=_fingerprint(proposal),
            findings=json.dumps(findings),
        )
        return _response(
            status="REJECTED" if findings else "REVIEW_PASSED",
            version=proposal.version,
            findings=findings,
            checks={
                requirement: _response(
                    name=name, passed=passed, status="PASS" if passed else "FAIL"
                )
                for requirement, name, passed in requirements
            },
        )

    def approve(
        self,
        proposal: _Proposal,
        approver: str,
        *,
        now: datetime | None = None,
        ttl: timedelta = timedelta(minutes=5),
    ) -> ApprovalRecord:
        self._check_pending(proposal)
        if approver == proposal.requester or approver != _ADMIN:
            self._deny("Independent synthetic administrator approval required")
        if self._reviewed != _fingerprint(proposal):
            self._deny("Passing review of the exact proposal required")
        if ttl <= timedelta(0) or ttl > timedelta(minutes=5):
            self._deny("Local approval must expire within five minutes")
        record = ApprovalRecord(
            approval_id=str(uuid4()),
            fingerprint=_fingerprint(proposal),
            approver=approver,
            scope=f"local-lifecycle/{proposal.template}/v{proposal.version}",
            approved=True,
            expires_at=(now or datetime.now(UTC)) + ttl,
        )
        self._issued[record.approval_id] = record
        self._record(
            "synthetic_admin_approved",
            approval_id=record.approval_id,
            fingerprint=record.fingerprint,
            approver=record.approver,
            expires_at=record.expires_at.isoformat(),
        )
        return record

    def _verify(
        self, proposal: _Proposal, approval: ApprovalRecord, now: datetime | None = None
    ) -> None:
        if (
            self._issued.get(approval.approval_id) != approval
            or not approval.approved
            or approval.approver != _ADMIN
            or approval.approver == proposal.requester
            or approval.fingerprint != _fingerprint(proposal)
            or approval.scope != f"local-lifecycle/{proposal.template}/v{proposal.version}"
            or approval.expires_at <= (now or datetime.now(UTC))
        ):
            self._deny("Approval missing, altered, expired, or not bound to the exact proposal")

    def publish(
        self, proposal: _Proposal, approval: ApprovalRecord, *, now: datetime | None = None
    ) -> dict[str, object]:
        self._check_pending(proposal)
        if self._reviewed != _fingerprint(proposal):
            self._deny("Passing review required before local publication receipt")
        self._verify(proposal, approval, now)
        receipt = _response(
            status="DRY_RUN",
            receipt_id=str(uuid4()),
            version=proposal.version,
            fingerprint=_fingerprint(proposal),
            approval_id=approval.approval_id,
            destination="LOCAL_RECEIPT_ONLY",
        )
        with (self.audit.path.parent / f"publication-v{proposal.version}.json").open(
            "x", encoding="utf-8"
        ) as file:
            json.dump(receipt, file, indent=2)
            file.write("\n")
        self._record(
            "local_dry_run_publication",
            approval_id=approval.approval_id,
            fingerprint=_fingerprint(proposal),
            version=str(proposal.version),
            status="DRY_RUN",
        )
        self.current_version = proposal.version
        self._published = proposal
        self._authorization = approval
        self.package_expires_at = (now or datetime.now(UTC)) + timedelta(
            days=proposal.package_duration_days
        )
        self._pending = None
        self._reviewed = None
        return receipt

    def access(self, tool: str, resource: str, mode: str = "READ_ONLY") -> dict[str, object]:
        allowed = (
            self._published is not None
            and self._authorization is not None
            and self.package_expires_at is not None
            and self.package_expires_at > datetime.now(UTC)
            and tool in self._published.tools
            and resource in self._published.resources
            and mode == self._published.mode == "READ_ONLY"
        )
        self._record(
            "local_access_permitted" if allowed else "local_access_denied",
            tool=tool,
            resource=resource,
            mode=mode,
        )
        return _response(
            status="READ_ONLY" if allowed else "BLOCKED",
            allowed=allowed,
            tool=tool,
            resource=resource,
            content="Synthetic local record only" if allowed else "No authorized local access",
        )


def run_lifecycle(state_dir: Path) -> dict[str, object]:
    """Persist an isolated synthetic lifecycle story; never call a platform or publisher."""
    run_id = str(uuid4())
    run_dir = state_dir / "lifecycle" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    lifecycle = _Lifecycle(run_dir, run_id)
    proposal = _Proposal(version=1)
    request = lifecycle.request(proposal)
    before = lifecycle.access(proposal.tools[0], proposal.resources[0])
    before_resources = [
        lifecycle.access(proposal.tools[0], resource) for resource in proposal.resources
    ]
    review = lifecycle.review(proposal)
    self_approval_refused = False
    try:
        lifecycle.approve(proposal, proposal.requester)
    except PermissionError:
        self_approval_refused = True
    approval = lifecycle.approve(proposal, _ADMIN)
    receipt = lifecycle.publish(proposal, approval)
    after = lifecycle.access(proposal.tools[0], proposal.resources[0])
    after_resources = [
        lifecycle.access(proposal.tools[0], resource) for resource in proposal.resources
    ]
    write = lifecycle.access(proposal.tools[0], proposal.resources[0], "WRITE")
    update = _Proposal(
        version=2,
        owner="",
        sponsor="",
        release_gate_passed=False,
        write_approval_required=False,
        open_outbound=True,
        clearance="Confidential",
        resources=(*_RESOURCES, "synthetic-out-of-package"),
    )
    lifecycle.request(update)
    update_review = lifecycle.review(update)
    failed_review_approval_refused = False
    try:
        lifecycle.approve(update, _ADMIN)
    except PermissionError:
        failed_review_approval_refused = True
    rejected_update_publication_refused = False
    try:
        lifecycle.publish(update, approval)
    except PermissionError:
        rejected_update_publication_refused = True
    audit_verified = verify_audit(lifecycle.audit.path, lifecycle.audit_head)
    checks = {
        "preapproval_access_denied": before["allowed"] is False,
        "all_preapproval_resources_denied": all(
            result["allowed"] is False for result in before_resources
        ),
        "self_approval_refused": self_approval_refused,
        "independent_approval": approval.approver != proposal.requester,
        "exact_approval_fingerprint": approval.fingerprint == _fingerprint(proposal),
        "expiring_approval": approval.expires_at > datetime.now(UTC),
        "postapproval_read_only_access": after["status"] == "READ_ONLY",
        "all_postapproval_resources_read_only": all(
            result["status"] == "READ_ONLY" for result in after_resources
        ),
        "write_access_denied": write["allowed"] is False,
        "failed_review_approval_refused": failed_review_approval_refused,
        "rejected_update_publication_refused": rejected_update_publication_refused,
        "prior_version_retained": lifecycle.current_version == 1,
        "audit_hash_chain_verified": audit_verified,
    }
    report_path = run_dir / "report.json"
    report = _response(
        status="PASS" if all(checks.values()) else "FAIL",
        run_id=run_id,
        current_version=lifecycle.current_version,
        policy_template={
            "name": proposal.template,
            "kind": _KIND,
            "platform_actions": "NOT_EXECUTED",
            "conceptual_microsoft_defaults": [
                "least privilege",
                "independent approval",
                "auditable lifecycle",
            ],
            "defaults_status": "CONCEPTUAL_ONLY_NOT_FETCHED_OR_ENFORCED",
            "conditional_access": proposal.conditional_access,
            "access_package": proposal.access_package,
            "attributes": list(proposal.attributes),
            "attributes_status": "DESCRIPTIVE_ONLY",
        },
        request=request,
        review=review,
        approval=_response(status="DRY_RUN", **approval.model_dump(mode="json")),
        local_access_package=_response(
            status="LOCAL_MOCK",
            duration_days=proposal.package_duration_days,
            expires_at=(
                lifecycle.package_expires_at.isoformat()
                if lifecycle.package_expires_at is not None
                else None
            ),
            resources=list(proposal.package_resources),
            authorization="LOCAL_ONLY_NOT_ENTRA_ENTITLEMENT",
        ),
        publication_receipt=receipt,
        access_before=before,
        access_after=after,
        resource_access_before=before_resources,
        resource_access_after=after_resources,
        update_review=update_review,
        review_findings=update_review["findings"],
        checks=checks,
        audit_path=str(lifecycle.audit.path),
        audit_head=lifecycle.audit_head,
        audit_verified=audit_verified,
        report_path=str(report_path),
        limitations=[
            "Synthetic local authority; not enterprise identity or administrative consent.",
            "No Agent 365, Entra, Conditional Access, access package, registry, or cloud actions.",
            "DRY_RUN publication is a local receipt, not publishing or registering an agent.",
            "The audit chain is locally verified, not externally anchored.",
        ],
    )
    with report_path.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    return report
