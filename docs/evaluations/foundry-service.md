# Microsoft Foundry evaluation path

Azure mode uses the stable Microsoft SDK:
`azure-ai-evaluation==1.18.12`, `RelevanceEvaluator`, `GroundednessEvaluator`,
and `evaluate(..., azure_ai_project=..., fail_on_evaluator_errors=True)`.
The judge is a real configured Azure model deployment; project result tracking
is requested through the supported SDK. Nothing here is an emulated Foundry API.

Configure the explicit evaluation endpoint, judge deployment and API version
in ignored `.env`. The evaluator API version is selected from current Microsoft
documentation for your judge deployment, not guessed by the application.
The default workload settings also require the project's tenant/subscription
and Search configuration. Azure Government service support remains
VERIFICATION_REQUIRED and this evaluator adapter currently rejects it.

```bash
uv sync --frozen --all-extras --dev
# Plan/configuration does not submit evaluation:
# After independently authorizing cost and synthetic dataset upload:
uv run fsa evaluate --mode azure --data data/evaluation/smoke.jsonl \
  --output artifacts/foundry-evaluation-run-01 --authorize
```

Reusing an output directory with existing raw evidence is rejected. Dataset rows
require unique case IDs, explicit synthetic classification, query, response and
context. SDK-returned records remain separate from application interpretation.
Exact case/row coverage, both required metric fields, finite scores and documented
1–5 relevance/groundedness semantics are validated. Below-threshold quality fails;
missing/invalid evidence is insufficient. Neither metric is a security guarantee:
the report always preserves `security_release: NOT_EVALUATED`.

The raw SDK result may contain input/response content. Keep it private in ignored
artifacts, never upload customer data under a synthetic label, and review retention
and costs before submitting. `project_upload: REQUESTED_NOT_INDEPENDENTLY_VERIFIED`
is not a claim that the portal was independently inspected.

## Open-source fallback

`uv run fsa evaluate --mode local` runs the deterministic pytest-compatible
synthetic evidence regression suite. It exercises verdict conflicts, missing tool
and span evidence, blocked attempts, unsafe execution despite a safe final answer,
evaluator errors and taxonomy mismatch. It is not a substitute measurement for
model-judged relevance or groundedness and is never labeled a Foundry service run.

The Microsoft evaluation SDK itself is open source, but this fallback requires
neither a remote model nor that optional SDK. Selecting local mode is explicit;
Azure evaluator errors propagate and cannot silently become local PASS.

Sources:
[SDK overview](https://learn.microsoft.com/python/api/overview/azure/ai-evaluation-readme),
[relevance](https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation.relevanceevaluator),
[groundedness](https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation.groundednessevaluator),
[SDK repository](https://github.com/Azure/azure-sdk-for-python).
