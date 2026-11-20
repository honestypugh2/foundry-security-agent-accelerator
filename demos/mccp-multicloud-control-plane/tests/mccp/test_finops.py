import unittest

from _mccp_helpers import REPO

from mccp.finops import (PriceTable, SpendLine, UsageRecord, budget_status, evaluate, forecast, limits_for, load_budgets, load_usage,
                         recommend)
from mccp.registry import FixtureAdapter

DATA = REPO / "data" / "mccp"


class FinopsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices = PriceTable.load(DATA / "prices.json")
        cls.usage = load_usage(DATA / "usage_fixture.jsonl")
        cls.agents = FixtureAdapter(DATA / "agents.json").list_agents()
        cls.budgets = load_budgets(DATA / "budgets.json")

    def test_prices_are_labelled_illustrative(self):
        self.assertIn("ILLUSTRATIVE", self.prices.label)

    def test_cost_math(self):
        self.assertAlmostEqual(self.prices.cost("gpt-4.1", 1_000_000, 1_000_000), 10.0)
        self.assertAlmostEqual(self.prices.blended_per_1m("gpt-4.1", 0.7), 3.8)
        self.assertEqual(self.prices.usd_to_tokens(40), 10_500_000)

    def test_status_thresholds(self):
        self.assertEqual(budget_status(79.99), "ok")
        self.assertEqual(budget_status(80), "warn")
        self.assertEqual(budget_status(99.9), "warn")
        self.assertEqual(budget_status(100), "breach")

    def test_recommendations(self):
        self.assertEqual(recommend("agent", "breach", 300, True), "kill")
        self.assertEqual(recommend("agent", "breach", 120, False), "throttle")
        self.assertEqual(recommend("user", "breach", 120, True), "approve increase")
        self.assertEqual(recommend("user", "warn", 150, False), "approve increase")
        self.assertEqual(recommend("agent", "ok", 50, False), "none")
        self.assertEqual(recommend("agent", "ok", 110, False), "notify owner")

    def test_linear_forecast(self):
        line = SpendLine("a", spend_mtd_usd=19.0)
        for d in range(1, 20):
            line.daily_usd[f"2026-11-{d:02d}"] = 1.0
        linear, burn, spike = forecast(line, "2026-11-20")
        self.assertAlmostEqual(linear, 30.0)
        self.assertAlmostEqual(burn, 30.0)
        self.assertFalse(spike)

    def test_fixture_story(self):
        views = {v.budget.key: v for v in evaluate(self.usage, self.prices, limits_for("agent", self.agents, self.budgets), "agent", "2026-11-20")}
        self.assertEqual(len(views), 6)
        coder = views["contoso-rev-cycle-coder"]
        self.assertEqual((coder.budget.status, coder.budget.recommended_action), ("breach", "kill"))
        self.assertTrue(coder.spike)
        self.assertEqual(views["contoso-patient-scheduling"].budget.status, "warn")
        self.assertEqual(views["contoso-claims-triage"].budget.status, "ok")
        users = {v.budget.key: v for v in evaluate(self.usage, self.prices, limits_for("user", self.agents, self.budgets), "user", "2026-11-20")}
        self.assertEqual(users["j.chen@contoso-health.example"].budget.recommended_action, "approve increase")

    def test_unknown_model_is_an_error(self):
        with self.assertRaises(KeyError):
            self.prices.cost("not-a-model", 1, 1)

    def test_usage_record_total(self):
        r = UsageRecord("2026-11-01", "a", "u", "cc", "azure", "foundry", "gpt-4.1", 10, 5)
        self.assertEqual(r.total_tokens, 15)


if __name__ == "__main__":
    unittest.main()
