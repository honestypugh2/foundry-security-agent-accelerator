"""The add-on is a self-contained folder: demos/mccp-multicloud-control-plane in the base repo."""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DemoFolderLayoutTest(unittest.TestCase):
    def test_standalone_project_files(self):
        for name in ("README.md", "pyproject.toml", "Makefile", ".gitignore", ".env.example"):
            self.assertTrue((ROOT / name).is_file(), name)
        for old in ("MERGE.md", "Makefile.mccp", "pyproject.mccp.toml", ".env.example.mccp"):
            self.assertFalse((ROOT / old).exists(), old)
        py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('pythonpath = ["src"]', py)
        self.assertIn('packages = ["src/mccp"]', py)

    def test_readme_unzips_into_new_demos_folder(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("git checkout -b feature/multicloud-control-plane", text)
        self.assertIn("mkdir -p demos/mccp-multicloud-control-plane", text)
        self.assertRegex(text, r"unzip -o .*mccp-multicloud-control-plane-addon\.zip.*\n\s*-d demos/mccp-multicloud-control-plane")
        commands = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("/tmp", commands)

    def test_nothing_written_outside_the_demo_folder(self):
        sh = (ROOT / "infra/mccp/deploy.sh").read_text(encoding="utf-8")
        self.assertNotIn("/tmp", sh)
        self.assertIn('ROOT="$(cd "$HERE/../.." && pwd)"', sh)
        self.assertIn('ENVF="$ROOT/.env.mccp.azure"', sh)
        self.assertIn('SMOKE="$OUTDIR/smoke-response.json"', sh)
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
        for entry in (".env", ".env.mccp.azure", "artifacts/", ".venv/"):
            self.assertIn(entry, ignored)

    def test_settings_paths_resolve_to_demo_folder_from_any_cwd(self):
        code = "from mccp.config import Settings, REPO_ROOT; s=Settings.from_env(); print(REPO_ROOT); print(s.data_dir); print(s.artifacts_dir)"
        env = {k: v for k, v in os.environ.items() if not k.startswith("MCCP_")}
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory() as elsewhere:
            out = subprocess.run([sys.executable, "-c", code], cwd=elsewhere, env=env, capture_output=True, text=True, check=True).stdout.split("\n")
        self.assertEqual(Path(out[0]), ROOT)
        self.assertEqual(Path(out[1]), ROOT / "data" / "mccp")
        self.assertEqual(Path(out[2]), ROOT / "artifacts" / "mccp")

    def test_docs_have_no_merge_or_root_copy_steps(self):
        for p in [ROOT / "README.md", *ROOT.glob("docs/mccp/*.md"), ROOT / "mccp/README.md", ROOT / "infra/mccp/README.md"]:
            text = p.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"cp -r \$ADDON|MERGE\.md|Makefile\.mccp|pyproject\.mccp", str(p))


if __name__ == "__main__":
    unittest.main()
