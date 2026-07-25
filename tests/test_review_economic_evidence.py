import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_economic_evidence.py"
SPEC = importlib.util.spec_from_file_location("review_economic_evidence", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReviewEconomicEvidenceTests(unittest.TestCase):
    def test_component_classification(self):
        component, confidence = MODULE.classify_component(
            "The filing reported €50 million in rebuilding costs after the outage."
        )
        self.assertEqual(component, "real_resource")
        self.assertGreater(confidence, 0.5)

    def test_fx_conversion_requires_explicit_rate(self):
        candidate = {
            "candidate_id": "cand_x",
            "event_id": "evt_0123456789abcdefabcd",
            "currency": "EUR",
            "amount_native": 10_000_000,
            "snippet": "Investment of €10 million.",
            "source_url": "https://example.eu/report",
        }
        enriched = MODULE.enrich(candidate, {"as_of": "2026-07-25", "rates_to_usd": {"USD": 1.0}})
        self.assertIsNone(enriched["amount_usd"])
        self.assertEqual(enriched["conversion_status"], "missing_rate")

    def test_promotion_requires_acceptance_and_attribution(self):
        candidate = {
            "candidate_id": "cand_x",
            "event_id": "evt_0123456789abcdefabcd",
            "observed_at": "2026-07-25T00:00:00+00:00",
            "amount_usd": 5_000_000,
            "component_suggestion": "capital_allocation",
            "overlap_group_suggestion": "evt_x:capital_allocation:abc",
            "source_url": "https://example.com/filing",
            "source_priority": "primary_hint",
        }
        self.assertIsNone(MODULE.promote(candidate, {"review_status": "pending"}))
        self.assertIsNone(MODULE.promote(candidate, {
            "review_status": "accepted",
            "attribution_probability": None,
        }))

        promoted = MODULE.promote(candidate, {
            "review_status": "accepted",
            "attribution_probability": 0.7,
            "component": "capital_allocation",
        })
        self.assertIsNotNone(promoted)
        self.assertEqual(promoted["gross_usd"], 5_000_000)
        self.assertEqual(promoted["attribution_probability"], 0.7)

    def test_overlap_suggestion_is_stable(self):
        first = MODULE.suggest_overlap("evt_x", "valuation", "Market cap fell by $2 billion.")
        second = MODULE.suggest_overlap("evt_x", "valuation", "Market cap fell by $2 billion.")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
