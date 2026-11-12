# Agent 365 troubleshooting

| Observation | Safe response |
|---|---|
| UNKNOWN in local mode | Expected; no cloud read occurred |
| VERIFICATION_REQUIRED without preview opt-in | Inspect current documentation; opt in only for an authorized account read |
| NotLicensed | Resolve license with administrators; do not relabel PASS |
| Enabled flag but no activity | Check applicable consent, agent type, product route and latency; retain missing-ingestion status |
| Registry missing | Verify supported publish/connect path and intended tenant; workload creation is not publication |
| Observation expired/wrong tenant or agent | Collect fresh scoped evidence, not a copied unrelated screenshot |
| Defender/Purview silent | Verify native supported signal/policy; no universal alert guarantee |
| Permission error | Request least-privilege review; do not bypass consent or broaden roles automatically |

Never paste access tokens or private configuration into a public issue.
Use identifiers/times in approved private support channels; public examples stay
synthetic. [Prerequisites](prerequisites.md), [signal matrix](signal-scope-matrix.md).
