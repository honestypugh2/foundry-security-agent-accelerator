"""Prepare an uncommitted participant snapshot; never publish or include Git/private state."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("src", "tests", "data", "agents", "notebooks", "scripts", "infra", "docs")
FILES = (
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    "uv.lock",
    "Makefile",
    ".gitignore",
    ".env.example",
    ".python-version",
    ".pre-commit-config.yaml",
    ".devcontainer/devcontainer.json",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/dependabot.yml",
    ".github/workflows/validate.yml",
    "azure.yaml",
    "docs/assets/readme-banner.png",
    "docs/assets/architecture/six-plane-reference.drawio",
    "docs/assets/architecture/six-plane-reference.svg",
    "docs/assets/architecture/six-plane-reference.html",
    "docs/assets/architecture/governed-function-flow.drawio",
    "docs/assets/architecture/governed-function-flow.svg",
    "docs/assets/screenshots/defender-synthetic-inventory.png",
    "docs/assets/screenshots/foundry-function-tools.png",
)
SUFFIXES = {".py", ".json", ".jsonl", ".toml", ".md", ".html", ".ipynb", ".bicep", ".txt"}
LOCAL_ONLY_FILES = {
    "APEX_Foundry_Security_Agent365_Nov12_2026.html",
    "RELEASE_MANIFEST.json",
    "IMPLEMENTATION_PLAN.md",
    "IMPLEMENTATION_STATUS.md",
    "VALIDATION_EVIDENCE.md",
    "L600_TECHNICAL_VALIDATION.md",
    "REQUIREMENTS_GAP_ANALYSIS.md",
    "REUSE_ASSESSMENT.md",
    "docs/APEX_ALIGNMENT_BASELINE.md",
    "docs/APEX_COWORK_ARTIFACT_INVENTORY.md",
    "docs/APEX_AUDIENCE_RELEASE_CANDIDATE.md",
    "docs/APEX_TODAY_DEMO_STEPS.md",
    "docs/APEX_DEMO_COMMANDS.md",
    "docs/TOMORROW_DRY_RUN_CHECKLIST.md",
    "docs/COWORK_VSCODE_ALIGNMENT.md",
    "docs/COWORK_LAB_ALIGNMENT.md",
    "docs/APEX_VALIDATION_RESULTS.md",
    "docs/APEX_AZURE_LIVE_RESULTS.md",
    "docs/AGENT365_INTEGRATION_STATUS.md",
    "docs/AGENT365_EXTENSION.md",
    "docs/LIVE_AZURE_SETUP.md",
    "docs/observability/correlation-model.md",
    "docs/observability/trace-completeness.md",
    "docs/evaluations/asr-limitations.md",
    "docs/evaluations/human-adjudication.md",
    "docs/evaluations/release-gates.md",
    "docs/evaluations/verdict-semantics.md",
    "docs/security/mcp-security.md",
    "docs/security/multi-agent-delegation.md",
    "docs/security/egress-security.md",
    "docs/security/evidence-assurance.md",
    "docs/clouds/compensating-controls.md",
    "docs/clouds/cross-cloud-governance.md",
    "docs/clouds/feature-availability.md",
    "docs/architecture/cross-cloud-governance-pattern.md",
    "docs/agent365/defender-integration.md",
    "docs/agent365/purview-integration.md",
    "docs/agent365/governance.md",
    "docs/agent365/identity-and-permissions.md",
    "docs/agent365/publishing-and-registry.md",
    "docs/agent365/telemetry.md",
    "docs/agent365/prerequisites.md",
    "docs/agent365/troubleshooting.md",
    "scripts/validate_html_browser.py",
}


def prepare(output: Path) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Use a new empty snapshot destination")
    if ROOT not in output.parents or output.parts[-2] != "artifacts":
        raise ValueError("Snapshot must be a named direct child of repository artifacts/")
    candidates = {ROOT / name for name in FILES if (ROOT / name).is_file()}
    for directory in DIRECTORIES:
        candidates.update(
            path
            for path in (ROOT / directory).rglob("*")
            if path.is_file()
            and path.suffix in SUFFIXES
            and not any(
                path.is_relative_to(ROOT / "docs" / directory) for directory in ("demo", "research")
            )
            and not any(
                part.startswith(".") or part == "__pycache__"
                for part in path.relative_to(ROOT).parts
            )
        )
    candidates = {
        path for path in candidates if path.relative_to(ROOT).as_posix() not in LOCAL_ONLY_FILES
    }
    output.mkdir(parents=True, exist_ok=False)
    entries: list[dict[str, str]] = []
    for path in sorted(candidates):
        relative = path.relative_to(ROOT)
        target = output / relative
        if path.is_symlink():
            raise ValueError("Release candidate cannot contain symlinks")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        entries.append(
            {"path": relative.as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        )
    manifest: dict[str, object] = {
        "status": "UNPUBLISHED_CANDIDATE_REQUIRES_OWNER_PROVENANCE_AND_CONTENT_CLEARANCE",
        "files": entries,
        "excluded": [
            "Git history and metadata",
            "private .env, cloud state and credentials",
            "generated artifacts and run evidence",
            "new supplied v2 presentation and technical HTML pending identifier/provenance review",
            "external Cowork materials",
            "presenter scripts, talk tracks, timing and internal alignment documents",
            "build/implementation records, local validation evidence and retired short notes",
        ],
    }
    (output / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"status": manifest["status"], "files": len(entries), "output": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))


if __name__ == "__main__":
    main()
