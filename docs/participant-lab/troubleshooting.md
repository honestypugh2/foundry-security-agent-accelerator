# Participant troubleshooting

| Symptom | Safe next step |
|---|---|
| `No module named fsa` | From repo root run frozen sync and `uv run python -m fsa doctor`; select `.venv`, not system Python |
| Notebook import error | Run `uv sync --frozen --all-extras --dev`; select the repository `.venv` interpreter; open from repo or its notebooks folder |
| PowerShell activation blocked | Use `uv run python -m fsa ...`; do not change machine policy |
| Offline dependency cache miss | Install frozen dependencies once while connected; local execution itself must not use services |
| Doctor passes but Azure fails | Doctor checks configuration only. Inspect private account selection, quota, RBAC, pinned version and network with the owner |
| Preflight exits nonzero | Capability evidence is unresolved; account match alone cannot pass every check |
| Whoami passes but SDK differs | CLI account selection is not proof of effective DefaultAzureCredential identity; review credential source privately |
| Ask guest denied | Expected synthetic entitlement boundary; do not broaden roles to make the lab pass |
| Email-retention question gets equipment example | Use `--profile presentation` for the fictional retention corpus; no retention result is authoritative legal guidance |
| Live notebook PermissionError | Consent was not given; stop or use notebook 06. Do not bypass authorization |
| Live notebook PARTIAL assertion | A required service/evidence check is incomplete; read the sanitized summary. Local passing tests cannot fill the gap |
| Awaiting approval / no receipt | Expected default; explicit local demo approval yields only DRY_RUN |
| Trace-check missing writer/approval | Expected for an awaiting-approval run; use the approved local demo or scene-aware rehearsal |
| Red-team strict exits 1 | Expected supplied unsafe/unknown fixture rejection; ordinary reconciliation exits 0 without certifying release |
| Agent 365 status not PASS | Read settings are not registry/activity validation; independently establish license, preview/cloud/permission eligibility |
| Missing portal signal | Record NOT OBSERVED/VERIFICATION_REQUIRED; no automatic enablement or inference |

Never paste private settings, credential errors, tokens, notebook outputs or
service addresses into public issues. Report sanitized error categories and the
exact command shape only. Keep original evidence private.
