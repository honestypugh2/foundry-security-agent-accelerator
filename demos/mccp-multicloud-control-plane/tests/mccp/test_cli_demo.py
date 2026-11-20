import json
import os
import subprocess
import sys
import unittest

from _mccp_helpers import REPO, cleanup, make_settings

from mccp.demo import run_demo_capture
from mccp.report import strip_ansi


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.settings = make_settings()

    def tearDown(self):
        cleanup(self.settings)

    def test_demo_story_end_to_end(self):
        out, summary = run_demo_capture(self.settings, color=True)
        self.assertIn("\x1b[", out)  # coloured
        text = strip_ansi(out)
        for n in range(1, 13):
            self.assertIn(f"SCENE {n:02d}", text)
        statuses = [c["status"] for c in summary["calls"]]
        self.assertGreaterEqual(statuses.count(200), 3)
        for code in (401, 403, 423, 429, 503):
            self.assertIn(code, statuses)
        self.assertLess(statuses.index(429), statuses.index(423))
        self.assertEqual(statuses[-1], 200)  # revived
        self.assertEqual(summary["named_values"]["killed-agents"], "none")
        self.assertEqual(summary["agents"], 6)
        self.assertTrue(all(os.path.isfile(p) for p in summary["receipts"]))

    def test_demo_is_deterministic(self):
        a, _ = run_demo_capture(self.settings)
        b, _ = run_demo_capture(self.settings)
        self.assertEqual(a, b)

    def _cli(self, *args):
        env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "MCCP_ARTIFACTS_DIR": str(self.settings.artifacts_dir), "NO_COLOR": "1"}
        return subprocess.run([sys.executable, "-m", "mccp", *args], cwd=REPO, env=env, capture_output=True, text=True, timeout=120)

    def test_cli_demo_runs(self):
        p = self._cli("demo", "--mode", "local")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SCENE 12", p.stdout)

    def test_cli_json_outputs(self):
        inv = json.loads(self._cli("inventory", "--format", "json").stdout)
        self.assertTrue(inv["simulated"])
        self.assertEqual(len(inv["agents"]), 6)
        spend = json.loads(self._cli("spend", "--scope", "user", "--format", "json").stdout)
        self.assertEqual(spend["scope"], "user")
        self.assertEqual(self._cli("policy-map").returncode, 0)

    def test_notebooks_are_valid_nbformat4(self):
        nbs = sorted((REPO / "notebooks" / "mccp").glob("*.ipynb"))
        self.assertEqual(len(nbs), 6)
        for nb in nbs:
            data = json.loads(nb.read_text(encoding="utf-8"))
            self.assertEqual(data["nbformat"], 4)
            self.assertTrue(any(c["cell_type"] == "markdown" for c in data["cells"]))
            code = "".join("".join(c["source"]) for c in data["cells"] if c["cell_type"] == "code")
            self.assertIn("RUN_LIVE = False", code)

    def test_infra_files_reference_documented_resources(self):
        foundry = (REPO / "infra" / "mccp" / "modules" / "foundry.bicep").read_text(encoding="utf-8")
        self.assertIn("Microsoft.CognitiveServices/accounts@2025-06-01", foundry)
        self.assertIn("allowProjectManagement: true", foundry)
        self.assertIn("'GlobalStandard'", foundry)
        apim = (REPO / "infra" / "mccp" / "modules" / "apim.bicep").read_text(encoding="utf-8")
        for token in ("__TPM_PER_AGENT__", "__AGENT_MONTHLY_TOKEN_QUOTA__", "__USER_MONTHLY_TOKEN_QUOTA__", "__USER_TIER2_MONTHLY_TOKEN_QUOTA__"):
            self.assertIn(token, apim)
            self.assertIn(token, (REPO / "infra" / "mccp" / "policies" / "ai-gateway.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
