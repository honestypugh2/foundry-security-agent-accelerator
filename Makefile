.PHONY: setup lint format-check typecheck test test-security eval verify-release-gate azure-preflight \
 azure-provision agent-deploy agent-run agent365-preflight agent365-status agent365-verify \
 protect-check prove-eval operate-trace demo-azure demo-local docs validate \
 azure-cleanup bicep dependency-scan secret-scan sbom notebooks

setup:
	uv sync --frozen --all-extras --dev
lint:
	uv run ruff check .
format-check:
	uv run ruff format --check .
typecheck:
	uv run pyright
test:
	uv run pytest --cov --cov-report=term-missing --cov-report=xml
test-security:
	uv run pytest -m "security or evaluation"
eval:
	uv run fsa evaluate
	uv run fsa eval --gate
verify-release-gate:
	uv run python scripts/verify_release_gate.py
azure-preflight:
	uv run fsa azure preflight
azure-provision:
	uv run fsa azure provision
azure-cleanup:
	uv run fsa azure cleanup
agent-deploy:
	uv run fsa agent deploy
agent-run:
	uv run fsa agent run
agent365-preflight:
	uv run fsa agent365 preflight
agent365-status:
	uv run fsa agent365 status
agent365-verify:
	uv run fsa agent365 verify $(if $(EVIDENCE),--evidence "$(EVIDENCE)",)
protect-check: test-security
prove-eval: eval
operate-trace:
	uv run fsa trace-check $(if $(TRACE),--trace "$(TRACE)",)
demo-azure:
	uv run fsa demo --mode azure --profile presentation --authorize
demo-local:
	uv run fsa demo --mode local --demo-approval
docs:
	uv run fsa open docs
bicep:
	az bicep build --file infra/main.bicep --stdout > /dev/null
	az bicep build --file infra/live.bicep --stdout > /dev/null
dependency-scan:
	uv run pip-audit --skip-editable
secret-scan:
	uv run python scripts/scan_public.py $(SCAN_ARGS)
sbom:
	uv export --frozen --all-extras --all-groups --format cyclonedx1.5 --output-file artifacts/sbom.cdx.json > /dev/null
notebooks:
	uv run python scripts/render_reference_architecture.py --check
	uv run python scripts/validate_notebooks.py --execute-local
validate: lint format-check typecheck test test-security eval verify-release-gate demo-local bicep secret-scan notebooks
