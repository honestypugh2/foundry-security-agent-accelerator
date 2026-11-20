import unittest

from _mccp_helpers import REPO, cleanup, make_settings

from mccp.models import AgentRecord
from mccp.registry import FixtureAdapter, build_inventory, merge, servicenow_payloads


class FakeAdapter:
    name = "fake"

    def __init__(self, agents):
        self.agents = agents

    def list_agents(self):
        return self.agents


class BrokenAdapter:
    name = "broken"

    def list_agents(self):
        raise RuntimeError("boom")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.settings = make_settings()

    def tearDown(self):
        cleanup(self.settings)

    def test_fixture_has_six_agents_across_three_clouds(self):
        agents = FixtureAdapter(REPO / "data" / "mccp" / "agents.json").list_agents()
        self.assertEqual(len(agents), 6)
        self.assertEqual({a.cloud for a in agents}, {"azure", "aws", "saas"})
        self.assertEqual({a.platform for a in agents}, {"foundry", "bedrock", "agentcore", "copilot_studio", "snowflake_cortex"})
        self.assertTrue(all(a.agent_id.startswith("contoso-") for a in agents))
        self.assertTrue(all(a.owner.endswith("@contoso-health.example") for a in agents))

    def test_invalid_platform_rejected(self):
        with self.assertRaises(ValueError):
            AgentRecord(agent_id="x", name="x", platform="gcp-vertex", cloud="azure", owner="o", cost_center="c")

    def test_merge_dedupes_and_enriches(self):
        fixture = [AgentRecord(agent_id="contoso-a", name="A", platform="foundry", cloud="azure", owner="o@x", cost_center="CC",
                               native_id="asst_1", sources=["fixture"])]
        live = [AgentRecord(agent_id="contoso-a-renamed", name="A", platform="foundry", cloud="azure", owner="", cost_center="",
                            native_id="asst_1", model="gpt-4.1", sources=["foundry"]),
                AgentRecord(agent_id="contoso-new", name="New", platform="bedrock", cloud="aws", owner="", cost_center="", sources=["bedrock"])]
        merged = merge(fixture, live)
        self.assertEqual([a.agent_id for a in merged], ["contoso-a", "contoso-new"])
        self.assertEqual(merged[0].model, "gpt-4.1")
        self.assertEqual(merged[0].owner, "o@x")
        self.assertEqual(merged[0].sources, ["fixture", "foundry"])

    def test_azure_mode_reports_adapter_failures_instead_of_fabricating(self):
        self.settings.mode = "azure"
        extra = AgentRecord(agent_id="contoso-live", name="Live", platform="foundry", cloud="azure", owner="", cost_center="", sources=["foundry"])
        agents, warnings = build_inventory(self.settings, [FakeAdapter([extra]), BrokenAdapter()])
        self.assertEqual(len(agents), 7)
        self.assertTrue(any("broken" in w for w in warnings))

    def test_servicenow_payload(self):
        agents, _ = build_inventory(self.settings)
        rows = servicenow_payloads(agents)
        self.assertEqual(len(rows), 6)
        self.assertIn("u_identity_okta_app_id", rows[0])
        self.assertEqual(rows[0]["u_status"], "active")


if __name__ == "__main__":
    unittest.main()
