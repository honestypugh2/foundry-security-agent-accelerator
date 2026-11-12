"""The only action sink: durable idempotent DRY_RUN receipts, never business writes."""

import sqlite3
from pathlib import Path
from uuid import uuid4

from .approvals import ApprovalService, fingerprint
from .contracts import ActionProposal, ApprovalRecord, WriterReceipt
from .policy import decide


class DryRunWriter:
    def __init__(self, path: Path, approvals: ApprovalService) -> None:
        self.path = path
        self.approvals = approvals
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS receipts (fingerprint TEXT PRIMARY KEY, id TEXT)"
            )

    def execute(self, proposal: ActionProposal, approval: ApprovalRecord) -> WriterReceipt:
        if decide(proposal).outcome == "DENY":
            raise PermissionError("Policy denied action")
        self.approvals.verify(proposal, approval)
        digest = fingerprint(proposal)
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("INSERT OR IGNORE INTO receipts VALUES (?, ?)", (digest, str(uuid4())))
            row = db.execute("SELECT id FROM receipts WHERE fingerprint = ?", (digest,)).fetchone()
        if row is None or not isinstance(row[0], str):
            raise RuntimeError("Durable receipt missing")
        return WriterReceipt(fingerprint=digest, receipt_id=row[0])
