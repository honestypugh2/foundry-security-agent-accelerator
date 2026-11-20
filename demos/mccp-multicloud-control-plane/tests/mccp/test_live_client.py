"""Azure-mode request shapes, checked without network calls."""

import unittest
from unittest import mock

from mccp import gateway, killswitch
from mccp.config import Settings
from mccp.models import AgentRecord


def azure_settings(**kw):
    base = dict(mode="azure", apim_gateway_url="https://gw.example", apim_resource_id="/subscriptions/s/resourceGroups/r/providers/Microsoft.ApiManagement/service/a")
    base.update(kw)
    return Settings(**base)


class LiveClientTests(unittest.TestCase):
    def test_defaults_match_bicep(self):
        s = Settings()
        self.assertEqual(s.foundry_model_deployment, "policy-model")
        self.assertEqual(s.identity_provider, "entra")

    def test_azure_body_uses_max_completion_tokens(self):
        b = gateway.azure_chat_body("hi", 300, "minimal")
        self.assertEqual(b["max_completion_tokens"], 300)
        self.assertNotIn("max_tokens", b)
        self.assertEqual(b["reasoning_effort"], "minimal")
        self.assertNotIn("reasoning_effort", gateway.azure_chat_body("hi", 10, ""))

    def test_chat_posts_to_gateway_path(self):
        s = azure_settings()
        agent = mock.Mock(spec=AgentRecord, agent_id="contoso-claims-triage", cloud="azure", cost_center="CC-1")
        with mock.patch.object(gateway, "http_json", return_value=(200, {}, {"usage": {}})) as h:
            gateway.GatewayClient(s).chat(agent, "tok", "hello", max_tokens=64)
        method, url, headers, body = h.call_args.args[:4]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "https://gw.example/ai/openai/deployments/policy-model/chat/completions?api-version=2025-04-01-preview")
        self.assertEqual(headers["x-agent-id"], "contoso-claims-triage")
        self.assertEqual(body["max_completion_tokens"], 64)

    def test_gateway_token_entra_default(self):
        with mock.patch("mccp.receipts.azure_token", return_value="entra-token") as t:
            self.assertEqual(gateway.gateway_token(azure_settings()), "entra-token")
        t.assert_called_once_with("https://cognitiveservices.azure.com/.default")
        self.assertEqual(gateway.gateway_token(azure_settings(), "explicit"), "explicit")

    def test_named_value_read_uses_list_value(self):
        s = azure_settings()
        with mock.patch.object(killswitch, "http_json", return_value=(200, {}, {"value": "a,b"})) as h:
            status, value = killswitch.read_named_value(s, "killed-agents", "tok")
        self.assertEqual((status, value), (200, "a,b"))
        method, url = h.call_args.args[:2]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/namedValues/killed-agents/listValue?api-version=2024-05-01"))

    def test_live_kill_continues_when_okta_not_configured(self):
        import tempfile
        from pathlib import Path
        from mccp.models import KillOrder
        from mccp.receipts import ReceiptWriter
        from mccp.registry import build_inventory
        with tempfile.TemporaryDirectory() as d:
            s = azure_settings(artifacts_dir=Path(d))
            agents, _ = build_inventory(Settings(artifacts_dir=Path(d)))
            with mock.patch.object(killswitch, "azure_token", return_value="tok"), \
                 mock.patch.object(killswitch, "http_json", side_effect=lambda m, *a, **k: (200, {}, {"value": "none"})):
                receipts = killswitch.KillSwitch(s, ReceiptWriter(Path(d) / "r")).execute(
                    KillOrder(scope="agent", target="contoso-claims-triage", reason="test", requested_by="tester"), agents, authorize=True)
        by_point = {r.enforcement_point: r.status for r in receipts}
        self.assertEqual(by_point.get("apim-named-value"), "APPLIED")
        self.assertIn("SKIPPED", by_point.values())


if __name__ == "__main__":
    unittest.main()
