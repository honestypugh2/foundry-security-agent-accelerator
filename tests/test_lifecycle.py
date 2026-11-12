import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from foundry_security_accelerator.audit import verify_audit
from foundry_security_accelerator.lifecycle import _ADMIN, _Lifecycle, _Proposal, run_lifecycle


def test_lifecycle_persists_isolated_honest_story(tmp_path: Path) -> None:
    first = run_lifecycle(tmp_path)
    second = run_lifecycle(tmp_path)
    assert first["status"] == "PASS"
    assert first["current_version"] == 1
    assert first["kind"] == "LOCAL_SIMULATION_NOT_AGENT365_OR_ENTRA"
    assert first["platform_actions"] == "NOT_EXECUTED"
    assert first["review_findings"]
    assert {finding.split(":")[0] for finding in first["review_findings"]} >= {
        "REQ01",
        "REQ03",
        "REQ04",
        "REQ05",
        "REQ06",
        "REQ07",
    }
    assert all(check["passed"] for check in first["review"]["checks"].values())
    assert first["update_review"]["checks"]["REQ02"]["passed"]
    assert len(first["resource_access_before"]) == 2
    assert all(result["status"] == "BLOCKED" for result in first["resource_access_before"])
    assert all(result["status"] == "READ_ONLY" for result in first["resource_access_after"])
    assert first["local_access_package"]["duration_days"] == 180
    assert first["run_id"] != second["run_id"]
    report_path = Path(str(first["report_path"]))
    assert json.loads(report_path.read_text()) == first
    assert not (report_path.parent / "publication-v2.json").exists()
    assert verify_audit(Path(str(first["audit_path"])), str(first["audit_head"]))
    with Path(str(first["audit_path"])).open("a") as file:
        file.write("{}\n")
    assert not verify_audit(Path(str(first["audit_path"])), str(first["audit_head"]))


def test_review_and_independent_approval_cannot_be_bypassed(tmp_path: Path) -> None:
    lifecycle = _Lifecycle(tmp_path, str(uuid4()))
    proposal = _Proposal(1)
    lifecycle.request(proposal)
    with pytest.raises(PermissionError, match="Passing review"):
        lifecycle.approve(proposal, _ADMIN)
    lifecycle.review(proposal)
    with pytest.raises(PermissionError, match="Independent"):
        lifecycle.approve(proposal, proposal.requester)
    with pytest.raises(PermissionError, match="Independent"):
        lifecycle.approve(proposal, "unrecognized-admin")
    with pytest.raises(PermissionError, match="changed"):
        lifecycle.approve(replace(proposal, mode="WRITE"), _ADMIN)
    for ttl in (timedelta(0), timedelta(minutes=6)):
        with pytest.raises(PermissionError, match="expire"):
            lifecycle.approve(proposal, _ADMIN, ttl=ttl)
    approval = lifecycle.approve(proposal, _ADMIN)
    lifecycle.publish(proposal, approval)
    with pytest.raises(PermissionError, match="stale"):
        lifecycle.publish(proposal, approval)
    update = _Proposal(2, resources=("*",))
    lifecycle.request(update)
    assert lifecycle.review(update)["status"] == "REJECTED"
    with pytest.raises(PermissionError, match="Passing review"):
        lifecycle.approve(update, _ADMIN)
    with pytest.raises(PermissionError, match="Passing review"):
        lifecycle.publish(update, approval)
    assert lifecycle.current_version == 1
    assert lifecycle.access(proposal.tools[0], proposal.resources[0])["status"] == "READ_ONLY"
    assert lifecycle.access("other-tool", proposal.resources[0])["status"] == "BLOCKED"
    assert lifecycle.access(proposal.tools[0], "other-resource")["status"] == "BLOCKED"
    write = lifecycle.access(proposal.tools[0], proposal.resources[0], "WRITE")
    assert write["status"] == "BLOCKED"


def test_approval_is_exact_expiring_and_issued_by_this_run(tmp_path: Path) -> None:
    lifecycle = _Lifecycle(tmp_path / "first", str(uuid4()))
    proposal = _Proposal(1)
    lifecycle.request(proposal)
    lifecycle.review(proposal)
    now = datetime.now(UTC)
    approval = lifecycle.approve(proposal, _ADMIN, now=now)
    with pytest.raises(PermissionError, match="changed"):
        lifecycle.publish(replace(proposal, attributes=()), approval)
    with pytest.raises(PermissionError, match="altered"):
        lifecycle.publish(proposal, approval.model_copy(update={"fingerprint": "0" * 64}), now=now)
    with pytest.raises(PermissionError, match="expired"):
        lifecycle.publish(proposal, approval, now=approval.expires_at)
    other = _Lifecycle(tmp_path / "second", str(uuid4()))
    other.request(proposal)
    other.review(proposal)
    with pytest.raises(PermissionError, match="missing"):
        other.publish(proposal, approval, now=now)
    assert lifecycle.current_version == other.current_version == 0
    assert not (tmp_path / "first" / "publication-v1.json").exists()
    lifecycle.publish(proposal, approval, now=now)
    assert lifecycle.current_version == 1
    update = _Proposal(2)
    lifecycle.request(update)
    lifecycle.review(update)
    with pytest.raises(PermissionError, match="exact proposal"):
        lifecycle.publish(update, approval, now=now)
    assert lifecycle.current_version == 1


@pytest.mark.parametrize(
    ("proposal", "requirement"),
    [
        (_Proposal(1, sponsor=""), "REQ01"),
        (_Proposal(1, agent_identity="maker"), "REQ02"),
        (_Proposal(1, release_gate_passed=False), "REQ03"),
        (_Proposal(1, write_approval_required=False), "REQ04"),
        (_Proposal(1, open_outbound=True), "REQ05"),
        (_Proposal(1, clearance="Confidential"), "REQ06"),
        (_Proposal(1, package_resources=()), "REQ07"),
    ],
)
def test_each_named_requirement_evaluates_proposal_fields(
    tmp_path: Path, proposal: _Proposal, requirement: str
) -> None:
    lifecycle = _Lifecycle(tmp_path, str(uuid4()))
    lifecycle.request(proposal)
    review = lifecycle.review(proposal)
    assert review["status"] == "REJECTED"
    assert review["checks"][requirement]["status"] == "FAIL"
    assert {key for key, value in review["checks"].items() if not value["passed"]} == {requirement}
    with pytest.raises(PermissionError, match="Passing review"):
        lifecycle.approve(proposal, _ADMIN)
