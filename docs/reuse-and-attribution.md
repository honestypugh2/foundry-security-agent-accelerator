# Reuse and attribution

Reviewed on 2026-11-11. Repository metadata is not a license: all three requested
repositories had null `licenseInfo`, but their actual `LICENSE` files contain MIT.
No customer data, experiment outputs, private meeting content or tenant values
were imported.

| Source | Commit | Reviewed material | Use here |
|---|---|---|---|
| [ready-enterprise-ai-platform](https://github.com/honestypugh2/ready-enterprise-ai-platform) | `c5dee2b1bb26c807c9d4cb793f3b61f90359cfb4` | `packages/retrieval/azure_search.py`, `factory.py`, LICENSE | Adapted server-side entitlement trimming and explicit local/Azure provider selection in `src/foundry_security_accelerator/retrieval.py`; focused filter, schema, mismatch and timeout tests |
| [HR policy knowledge, requested branch](https://github.com/honestypugh2/foundry-copilot-hr-policy-knowledge/tree/bp/ai-governance-oct28) | `8fa394d8edca7b3c7c666077f25df3e4b65310b5` | `docs/RetrievalPatterns.md`, LICENSE, tree | Architecture reference only: distinguish direct index retrieval, managed prompt agents and self-hosted runtimes. No HR documents or experiment records reused |
| [ai-governance-operating-model](https://github.com/honestypugh2/ai-governance-operating-model) | `9d845e7876bdd02b32997128d86280edda415f71` | `pyproject.toml`, LICENSE, tree | Architecture/dependency reference: Python 3.12, Projects 2.10, Azure identity/telemetry, explicit synthetic/live distinction. No private operational content copied |

The Search adaptation is synchronous, small and strictly typed; its fixture schema
is synthetic-only. It uses equality disjunctions instead of comma-delimited
`search.in`, checks response entitlements again, and propagates errors rather than
silently switching providers. It does not import the source's broad exception
catches, `Any`-based interfaces, customer data or deployment configuration.

## License notice for the adapted Search pattern

MIT License

Copyright (c) 2026 Brittany Pugh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
