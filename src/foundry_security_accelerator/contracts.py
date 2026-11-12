"""Immutable boundary contracts. Evidence outcomes never imply unobserved execution."""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Outcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_EVALUATED = "NOT_EVALUATED"


class UserRequest(Contract):
    text: str = Field(min_length=1, max_length=4000)
    subject: str = Field(min_length=1)
    entitlements: frozenset[str] = frozenset({"employee"})
    correlation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        pattern=r"^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$",
    )


class RetrievedEvidence(Contract):
    source_id: str
    title: str
    content: str
    entitlement: str
    classification: Literal["synthetic"] = "synthetic"
    trusted: Literal[False] = False


class SecurityDecision(Contract):
    allowed: bool
    reason: str
    control: str


class ToolRequest(Contract):
    name: str
    arguments: dict[str, str] = Field(default_factory=dict)


class ToolResult(Contract):
    name: str
    status: Literal["READ_ONLY", "BLOCKED"]
    content: str


class PolicyDecision(Contract):
    outcome: Literal["ALLOW", "DENY", "REQUIRE_APPROVAL"]
    reason: str
    policy_version: str = "equipment-policy/1"


class ActionProposal(Contract):
    action: Literal["equipment_request"] = "equipment_request"
    subject: str = Field(min_length=1)
    item: str = Field(min_length=1, max_length=120)
    amount: int = Field(ge=1, le=100000)
    scope: Literal["synthetic-equipment"] = "synthetic-equipment"


class ApprovalRecord(Contract):
    approval_id: str
    fingerprint: str
    approver: str
    scope: str
    approved: bool
    expires_at: datetime


class ExecutionEvidence(Contract):
    attempt_id: str
    tool: str
    attempted: bool
    blocked: bool
    executed: bool | None
    critical: bool = True


class EvaluatorVerdict(Contract):
    evaluator: str
    outcome: Outcome
    critical: bool = True
    deterministic: bool = False
    error: str | None = None
    raw_record: str = "{}"
    taxonomy: str = "fsa/1"


class EvaluationEvidence(Contract):
    case_id: str
    verdicts: tuple[EvaluatorVerdict, ...]
    executions: tuple[ExecutionEvidence, ...] = ()
    required_tools: tuple[str, ...] = ()
    required_stages: tuple[str, ...] = ()
    observed_stages: tuple[str, ...] = ()
    taxonomy: str = "fsa/1"


class VerdictConsistencyResult(Contract):
    outcome: Outcome
    reasons: tuple[str, ...]


class HumanAdjudication(Contract):
    case_id: str
    reviewer: str = Field(min_length=1)
    rationale: str = Field(min_length=10)
    outcome: Outcome
    evidence_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    recorded_at: datetime


class TraceCompletenessResult(Contract):
    outcome: Outcome
    missing: tuple[str, ...]


class AuditReceipt(Contract):
    sequence: int
    correlation_id: str
    event: str
    data: dict[str, str]
    previous_hash: str
    hash: str


class ReleaseGateDecision(Contract):
    outcome: Outcome
    reasons: tuple[str, ...]


class WriterReceipt(Contract):
    fingerprint: str
    status: Literal["DRY_RUN"] = "DRY_RUN"
    receipt_id: str
