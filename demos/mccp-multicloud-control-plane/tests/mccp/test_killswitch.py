import json
import unittest
from pathlib import Path

from _mccp_helpers import cleanup, make_settings

from mccp.demo import build_local_runtime
from mccp.killswitch import (DEFAULT_POINTS, KillSwitch, approve_quota_increase, csv_add, csv_remove, named_value_request,
                             subscription_request)
from mccp.models import KillOrder
from mccp.receipts import ReceiptWriter

AGENT = "contoso-rev-cycle-coder"


class KillSwitchTests(unittest.TestCase):
    def setUp(self):
        self.settings = make_settings()
        self.rt = build_local_runtime(self.settings)
        self.writer = ReceiptWriter(self.settings.receipts_dir)
        self.ks = KillSwitch(self.settings, self.writer, self.rt.simulator)

    def tearDown(self):
        cleanup(self.settings)

    def order(self, scope="agent", target=AGENT, revive=False):
        return KillOrder(scope=scope, target=target, reason="test", requested_by="tester@contoso-health.example", revive=revive)

    def test_csv_helpers(self):
        self.assertEqual(csv_add("none", "a"), "a")
        self.assertEqual(csv_add("a", "a"), "a")
        self.assertEqual(csv_add("a", "b"), "a,b")
        self.assertEqual(csv_remove("a,b", "a"), "b")
        self.assertEqual(csv_remove("a", "a"), "none")

    def test_without_authorize_everything_is_dry_run_and_state_unchanged(self):
        receipts = self.ks.execute(self.order(), self.rt.agents, authorize=False)
        self.assertTrue(receipts)
        self.assertTrue(all(r.status in {"DRY_RUN", "SKIPPED", "MANUAL"} for r in receipts))
        self.assertEqual(self.rt.simulator.named_values.killed_agents, "none")
        for r in receipts:
            data = json.loads(Path(r.path).read_text(encoding="utf-8"))
            self.assertEqual(data["target"], AGENT)

    def test_order_gateway_then_identity_then_record(self):
        names = [p.name for p in DEFAULT_POINTS]
        self.assertLess(names.index("apim-named-value"), names.index("okta"))
        self.assertLess(names.index("okta"), names.index("servicenow"))
        receipts = self.ks.execute(self.order(), self.rt.agents, authorize=True)
        points = [r.enforcement_point for r in receipts]
        self.assertEqual(points[0], "apim-named-value")
        self.assertLess(points.index("okta"), points.index("servicenow"))

    def test_authorized_local_kill_blocks_with_423_and_revive_restores(self):
        self.ks.execute(self.order(), self.rt.agents, authorize=True)
        self.assertEqual(self.rt.simulator.named_values.killed_agents, AGENT)
        self.assertEqual(self.rt.call(AGENT, "p.nair@contoso-health.example", "hi").status, 423)
        self.assertEqual(next(a for a in self.rt.agents if a.agent_id == AGENT).status, "killed")
        self.ks.execute(self.order(revive=True), self.rt.agents, authorize=True)
        self.assertEqual(self.rt.call(AGENT, "p.nair@contoso-health.example", "hi").status, 200)

    def test_external_points_never_live_in_local_mode(self):
        receipts = self.ks.execute(self.order(target="contoso-patient-scheduling"), self.rt.agents, authorize=True, hard=True)
        by_point = {r.enforcement_point: r.status for r in receipts}
        self.assertEqual(by_point["okta"], "DRY_RUN")
        self.assertEqual(by_point["servicenow"], "DRY_RUN")
        self.assertEqual(by_point["aws-iam"], "DRY_RUN")
        self.assertEqual(by_point["apim-subscription"], "SIMULATED")
        self.assertEqual(self.rt.call("contoso-patient-scheduling", "r.silva@contoso-health.example", "hi").status, 401)

    def test_global_and_user_scopes(self):
        self.ks.execute(self.order("global", "*"), self.rt.agents, authorize=True)
        self.assertEqual(self.rt.call("contoso-claims-triage", "maria.gomez@contoso-health.example", "hi").status, 503)
        self.ks.execute(self.order("global", "*", revive=True), self.rt.agents, authorize=True)
        self.ks.execute(self.order("user", "maria.gomez@contoso-health.example"), self.rt.agents, authorize=True)
        self.assertEqual(self.rt.call("contoso-claims-triage", "maria.gomez@contoso-health.example", "hi").status, 423)
        self.assertEqual(self.rt.call("contoso-claims-triage", "k.ito@contoso-health.example", "hi").status, 200)

    def test_saas_agent_kill_gives_manual_platform_steps(self):
        receipts = self.ks.execute(self.order(target="contoso-hr-helpdesk"), self.rt.agents, authorize=False)
        manual = [r for r in receipts if r.status == "MANUAL"]
        self.assertEqual(len(manual), 1)
        self.assertIn("does NOT route through the APIM gateway", manual[0].detail["steps"][0])

    def test_arm_request_shapes(self):
        self.settings.apim_resource_id = "/subscriptions/s/resourceGroups/rg/providers/Microsoft.ApiManagement/service/apim"
        req = named_value_request(self.settings, "killed-agents", "a,b")
        self.assertEqual(req["method"], "PUT")
        self.assertEqual(req["url"], "https://management.azure.com/subscriptions/s/resourceGroups/rg/providers/Microsoft.ApiManagement"
                                     "/service/apim/namedValues/killed-agents?api-version=2024-05-01")
        self.assertEqual(req["body"], {"properties": {"displayName": "killed-agents", "value": "a,b", "secret": False}})
        sub = subscription_request(self.settings, "agent-x", "suspended")
        self.assertEqual((sub["method"], sub["body"]), ("PATCH", {"properties": {"state": "suspended"}}))

    def test_azure_mode_without_authorize_makes_no_calls(self):
        settings = make_settings("azure")
        try:
            ks = KillSwitch(settings, ReceiptWriter(settings.receipts_dir), None)
            receipts = ks.execute(self.order(), self.rt.agents, authorize=False)
            self.assertTrue(all(r.status in {"DRY_RUN", "SKIPPED", "MANUAL"} for r in receipts))
            okta = next(r for r in receipts if r.enforcement_point == "okta")
            self.assertTrue(okta.request["url"].endswith("/api/v1/apps/0oaSIMrevcyc0002/lifecycle/deactivate"))
        finally:
            cleanup(settings)

    def test_approval_raises_user_quota(self):
        sim = self.rt.simulator
        before = sim.user_quota_limit("j.chen@contoso-health.example")
        dry = approve_quota_increase(self.settings, self.writer, "j.chen@contoso-health.example", False, "k.ito", sim)
        self.assertEqual(dry.status, "DRY_RUN")
        self.assertEqual(sim.user_quota_limit("j.chen@contoso-health.example"), before)
        ok = approve_quota_increase(self.settings, self.writer, "j.chen@contoso-health.example", True, "k.ito", sim)
        self.assertEqual(ok.status, "SIMULATED")
        self.assertGreater(sim.user_quota_limit("j.chen@contoso-health.example"), before)


if __name__ == "__main__":
    unittest.main()
