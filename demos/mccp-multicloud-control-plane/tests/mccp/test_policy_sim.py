import unittest

from _mccp_helpers import REPO

from mccp.policy_sim import (XML_ELEMENT_MAP, GatewayRequest, NamedValues, PolicyConfig, PolicySimulator, SimClock,
                             make_local_token)

XML = (REPO / "infra" / "mccp" / "policies" / "ai-gateway.xml").read_text(encoding="utf-8")


class PolicySimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = PolicyConfig(tpm_per_agent=1_000, agent_monthly_token_quota=50_000, user_monthly_token_quota=2_000,
                                user_tier2_monthly_token_quota=10_000)
        self.sim = PolicySimulator(self.cfg, NamedValues(), SimClock())

    def token(self, agent="contoso-a", sub="u1", **over):
        now = self.sim.clock.epoch()
        claims = {"iss": self.cfg.okta_issuer, "aud": self.cfg.okta_audience, "sub": sub, "agent_id": agent, "cid": "0oa1",
                  "iat": now, "nbf": now, "exp": now + 600}
        claims.update(over)
        return make_local_token(claims)

    def req(self, token, agent="contoso-a", prompt="hello world", max_tokens=50, **headers):
        h = {"Authorization": f"Bearer {token}", "x-agent-id": agent, "x-cloud": "azure", "x-cost-center": "CC-1"}
        h.update(headers)
        return GatewayRequest(headers=h, body={"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})

    def test_allowed_call_sets_headers_and_emits_metric(self):
        r = self.sim.handle(self.req(self.token()))
        self.assertEqual(r.status, 200)
        for h in ("x-remaining-tokens", "x-agent-remaining-quota-tokens", "x-tokens-consumed", "x-user-remaining-quota-tokens"):
            self.assertIn(h, r.headers)
        self.assertEqual(len(self.sim.metrics), 1)
        self.assertEqual(set(self.sim.metrics[0]["dimensions"]), {"API ID", "agent-id", "user-id", "cloud", "cost-center"})
        self.assertEqual(self.sim.metrics[0]["dimensions"]["agent-id"], "contoso-a")

    def test_missing_and_invalid_tokens_return_401(self):
        self.assertEqual(self.sim.handle(GatewayRequest(headers={}, body={})).status, 401)
        self.assertEqual(self.sim.handle(self.req(self.token(aud="api://other"))).status, 401)
        self.assertEqual(self.sim.handle(self.req(self.token(iss="https://evil.example"))).status, 401)
        self.assertEqual(self.sim.handle(self.req(self.token(exp=self.sim.clock.epoch() - 1))).status, 401)

    def test_identity_mismatch_returns_403(self):
        r = self.sim.handle(self.req(self.token(agent="contoso-a"), agent="contoso-b"))
        self.assertEqual((r.status, r.body["error"]), (403, "agent_identity_mismatch"))

    def test_global_kill_503_and_killed_agent_423_and_killed_user_423(self):
        self.sim.named_values.killswitch_global = "true"
        self.assertEqual(self.sim.handle(self.req(self.token())).status, 503)
        self.sim.named_values.killswitch_global = "false"
        self.sim.named_values.killed_agents = "contoso-x, contoso-a"
        r = self.sim.handle(self.req(self.token()))
        self.assertEqual((r.status, r.body["error"]), (423, "agent_killed"))
        self.sim.named_values.killed_agents = "contoso-ab"  # no substring match
        self.assertEqual(self.sim.handle(self.req(self.token())).status, 200)
        self.sim.named_values.killed_users = "u1"
        self.assertEqual(self.sim.handle(self.req(self.token())).body["error"], "user_killed")

    def test_tpm_429_then_next_minute_allowed(self):
        prompt = "x" * 1600  # ~404 prompt tokens
        statuses = [self.sim.handle(self.req(self.token(sub="burst"), prompt=prompt, max_tokens=10)).status for _ in range(4)]
        self.assertIn(429, statuses)
        self.sim.clock.advance(60)
        self.assertEqual(self.sim.handle(self.req(self.token(sub="burst"), prompt=prompt, max_tokens=10)).status, 200)

    def test_user_monthly_quota_403_and_tier2_approval(self):
        prompt = "y" * 1200
        last = None
        for _ in range(20):
            last = self.sim.handle(self.req(self.token(), prompt=prompt, max_tokens=10))
            self.sim.clock.advance(61)
            if last.status != 200:
                break
        self.assertEqual((last.status, last.body["error"]), (403, "user_token_quota_exceeded"))
        self.sim.named_values.quota_tier2_users = "u1"
        self.assertEqual(self.sim.handle(self.req(self.token(), prompt=prompt, max_tokens=10)).status, 200)

    def test_subscription_suspended_blocks_before_policy(self):
        self.sim.suspended_subscriptions.add("agent-a")
        r = self.sim.handle(self.req(self.token(), **{"x-sim-apim-subscription": "agent-a"}))
        self.assertEqual((r.status, r.decided_by), (401, "apim:subscription-state"))

    def test_every_mapped_element_exists_in_xml_and_simulator(self):
        for tag, fn in XML_ELEMENT_MAP:
            self.assertIn(tag, XML, f"{tag} missing from ai-gateway.xml")
            self.assertTrue(hasattr(PolicySimulator, fn), fn)

    def test_xml_uses_documented_llm_token_limit_attributes(self):
        for attr in ('counter-key=', 'tokens-per-minute=', 'token-quota=', 'token-quota-period="Monthly"', 'estimate-prompt-tokens="true"',
                     'remaining-quota-tokens-header-name=', 'remaining-tokens-header-name=', 'tokens-consumed-header-name='):
            self.assertIn(attr, XML)
        self.assertIn('<authentication-managed-identity resource="https://cognitiveservices.azure.com" />', XML)
        self.assertIn("/.well-known/openid-configuration", XML)

    def test_xml_structure(self):
        # APIM "rawxml" allows double quotes inside @(...) expressions, so the file is not strict XML: check structure instead.
        positions = [XML.index(t) for t in ("<policies>", "<inbound>", "</inbound>", "<backend>", "<outbound>", "<on-error>", "</policies>")]
        self.assertEqual(positions, sorted(positions))
        for tag in ("choose", "when", "return-response", "validate-jwt", "llm-emit-token-metric"):
            self.assertEqual(XML.count(f"<{tag}>") + XML.count(f"<{tag} "), XML.count(f"</{tag}>"), tag)

if __name__ == "__main__":
    unittest.main()
