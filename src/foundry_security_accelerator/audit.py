"""Hash-linked append-only per-run evidence. External anchoring is required against rewriting."""

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from .contracts import AuditReceipt
from .security import redact


def _digest(
    sequence: int, correlation_id: str, event: str, data: dict[str, str], previous: str
) -> str:
    value = json.dumps(
        [sequence, correlation_id, event, data, previous], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(value.encode()).hexdigest()


class AuditLog:
    def __init__(self, path: Path, correlation_id: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidental evidence overwrite or mixing concurrent runs.
        with path.open("x", encoding="utf-8"):
            pass
        self.path = path
        self.correlation_id = correlation_id
        self._previous = "0" * 64
        self._sequence = 0

    def append(self, event: str, data: dict[str, str]) -> AuditReceipt:
        safe = {redact(key): redact(value) for key, value in data.items()}
        safe_event = redact(event)
        digest = _digest(self._sequence, self.correlation_id, safe_event, safe, self._previous)
        receipt = AuditReceipt(
            sequence=self._sequence,
            correlation_id=self.correlation_id,
            event=safe_event,
            data=safe,
            previous_hash=self._previous,
            hash=digest,
        )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(receipt.model_dump_json() + "\n")
            file.flush()
        self._previous = digest
        self._sequence += 1
        return receipt


def audit_failure_line(path: Path, expected_head: str | None = None) -> int | None:
    previous = "0" * 64
    count = 0
    correlation_id: str | None = None
    line_number = 1
    try:
        with path.open(encoding="utf-8") as file:
            for index, line in enumerate(file):
                line_number = index + 1
                record = AuditReceipt.model_validate_json(line)
                correlation_id = correlation_id or record.correlation_id
                if (
                    record.sequence != index
                    or record.correlation_id != correlation_id
                    or record.previous_hash != previous
                    or record.hash
                    != _digest(
                        index,
                        record.correlation_id,
                        record.event,
                        record.data,
                        previous,
                    )
                ):
                    return line_number
                previous = record.hash
                count += 1
    except (ValidationError, ValueError):
        return line_number
    if not count:
        return 1
    if expected_head is not None and previous != expected_head:
        return count + 1
    return None


def verify_audit(path: Path, expected_head: str | None = None) -> bool:
    return audit_failure_line(path, expected_head) is None
