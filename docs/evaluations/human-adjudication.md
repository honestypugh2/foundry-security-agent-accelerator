# Human adjudication

The `adjudicate` helper appends a separate record containing case, reviewer,
substantive rationale, chosen outcome, UTC timestamp and SHA-256 digest of the
original normalized evidence. The original verdicts remain unchanged.

This helper records an application-level adjudication; it does not authenticate
the reviewer or integrate with a production case-management system. Protect the
evidence and append-only adjudication store and authenticate reviewers externally.

Review conflicting model assessments against raw observations, policy versions,
tool execution and trace completeness. An adjudication cannot erase confirmed
unsafe execution or authorize a business write. A release override requires a
separate governed risk decision, not replacing FAIL with PASS in a raw record.
