import hashlib
import json
import runpy
from pathlib import Path

import pytest


def test_candidate_scanner_checks_exact_files_and_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scanner = runpy.run_path("scripts/scan_public.py")
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "example.py"
    source.write_text("print('synthetic')\n")
    manifest = tmp_path / "RELEASE_MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
                ]
            }
        )
    )
    assert scanner["main"](manifest) == 0
    source.write_text("changed after review\n")
    with pytest.raises(ValueError, match="differs"):
        scanner["main"](manifest)
    manifest.write_text(json.dumps({"files": [{"path": "../outside.py", "sha256": ""}]}))
    with pytest.raises(ValueError, match="Invalid"):
        scanner["main"](manifest)


def test_snapshot_refuses_overwrite_or_unbounded_destination(tmp_path: Path) -> None:
    module = runpy.run_path("scripts/prepare_audience_release.py")
    with pytest.raises(FileExistsError):
        module["prepare"](tmp_path)
    with pytest.raises(ValueError, match="artifacts"):
        module["prepare"](tmp_path / "not-a-repository-destination")


def test_snapshot_keeps_labs_but_excludes_local_presenter_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = runpy.run_path("scripts/prepare_audience_release.py")
    monkeypatch.setitem(module["prepare"].__globals__, "ROOT", tmp_path)
    private = (
        "PUBLIC_RELEASE_READINESS.md",
        "IMPLEMENTATION_STATUS.md",
        "REQUIREMENTS_GAP_ANALYSIS.md",
        "VALIDATION_EVIDENCE.md",
        "APEX_Foundry_Security_Agent365_Nov12_2026.html",
        "docs/AGENT365_INTEGRATION_STATUS.md",
        "docs/observability/correlation-model.md",
        "docs/research/source-to-code-mapping.md",
        "docs/demo/live-presenter-runbook.md",
        "docs/demo/live-presenter-exact-script.md",
        "docs/demo/future-talk-track.md",
        "docs/APEX_TODAY_DEMO_STEPS.md",
        "docs/APEX_DEMO_COMMANDS.md",
        "docs/TOMORROW_DRY_RUN_CHECKLIST.md",
        "docs/COWORK_VSCODE_ALIGNMENT.md",
        ".presenter/portal-talk-track.md",
    )
    public = (
        "src/workshop.py",
        "docs/participant-lab/local-fallback.md",
        "docs/assets/architecture/six-plane-reference.drawio",
        "docs/assets/architecture/six-plane-reference.svg",
        "docs/assets/architecture/six-plane-reference.html",
        "docs/assets/architecture/governed-function-flow.drawio",
        "docs/assets/architecture/governed-function-flow.svg",
        "docs/assets/screenshots/defender-synthetic-inventory.png",
        "docs/assets/screenshots/foundry-function-tools.png",
    )
    private += (
        "docs/assets/screenshots/private-portal-capture.png",
        "docs/assets/architecture/private-tenant-state.drawio",
        "docs/research/native-evidence.svg",
    )
    for relative in private + public:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original local training material\n")
    output = tmp_path / "artifacts" / "workshop"
    module["prepare"](output)
    manifest = json.loads((output / "RELEASE_MANIFEST.json").read_text())
    assert {entry["path"] for entry in manifest["files"]} == set(public)
    assert all(not (output / relative).exists() for relative in private)
