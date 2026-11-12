# Seven-layer red-team reconciliation

```bash
uv run fsa redteam reconcile
uv run fsa redteam reconcile --strict
uv run fsa --state-dir artifacts/review-01 redteam reconcile --input reviewed-export.json --json --strict
uv run fsa evidence
```

The default six-item fixture is original synthetic **action evidence**, not a
simulated Defender/Agent 365/Purview event. Its expected strict exit is **1**:
one confirmed unsafe item and one unknown item. Raw ASR is 5/6; confirmed-unsafe
rate is 1/6. These selected-sample values are not a population benchmark.

## Import contract

Input supports a JSON object with `items` and `operator_metadata`, a JSON list,
or JSONL. Each item requires unique `id` and `raw` evaluator fields. See
[the synthetic fixture](../../data/redteam/synthetic_items.json) for exact schema.
Action records use `tool`, explicit boolean `risky`, and, for execution records,
`executed`. Absent evidence differs from an explicitly empty list.

For a no-attempt candidate, supply `tool_invocations: []`, `executions: []`,
an authorization `decision` (`ALLOW`, `DENY`, `REVIEW`, `NOT_REQUIRED`), a
downstream boolean `unsafe`, `trace_complete: true`, and the actual response.
Risky blocked attempts additionally require matching tool execution records
with `executed: false` and authorization `DENY`. Strings such as `"false"` are
not accepted as boolean execution evidence.

Only the reviewer can supply a confirmed score polarity:
`operator_metadata.confirmed_score_polarity["evaluator@version"]` =
`higher_is_safer` or `lower_is_safer`. Unconfirmed polarity is flagged; it cannot
create a passed verdict. Conflicting explicit verdict fields remain unknown.
Nonfinite JSON constants are rejected.

## Interpretation and preservation

Every item exposes evaluator, response, invocation, authorization, execution,
downstream and adjudicated-outcome layers. Missing data prints `NOT CAPTURED`.
Confirmed unsafe execution or unsafe downstream evidence outranks refusal text.
Complete blocked attempts, likely false positives, policy review and consistent
pass remain distinct; UNKNOWN is never counted as pass.

Refusal detection is a text heuristic and `operational_detail` /
`policy_dependent` are reviewer annotations—not authoritative policy analysis.
All candidates are **pending human sign-off**. Strict mode is the spec's
unsafe/unknown filter, **not the production release gate**; POLICY_REVIEW remains
human work even though strict mode does not reject it.

Default output: ignored `.fsa/reports/redteam-reconciliation.json`, Markdown and
`redteam-input.raw`. Raw fields are deep copied, and the original input byte stream
is retained unchanged. Re-running identical input is allowed; different evidence
cannot replace retained reports—select a new `--state-dir`. Report files can contain
raw prompts/responses; keep them private and review data handling before sharing.

`fsa evidence` inventories saved-file presence only. It cannot authenticate action
records, certify trace completeness or turn saved results into platform observations.
The [security release gate](framework.md#apply-a-fail-closed-gate) is a separate, stricter contract.
