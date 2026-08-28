import unittest
from pathlib import Path

import yaml

from scripts import monitor


ROOT = Path(__file__).resolve().parents[1]


def load_watchgraph_rules() -> dict:
    rules = yaml.safe_load((ROOT / "config" / "rules.yaml").read_text(encoding="utf-8"))
    rules["_watchgraph"] = yaml.safe_load((ROOT / "config" / "watchgraph.yaml").read_text(encoding="utf-8"))
    rules["_watchgraph_markets"] = yaml.safe_load(
        (ROOT / "config" / "watchgraph_markets.yaml").read_text(encoding="utf-8")
    )
    return rules


class MonitorScoringTests(unittest.TestCase):
    def test_source_keywords_do_not_double_count_global_terms(self):
        keywords_config = {
            "keywords": [
                {"term": "AI", "aliases": ["AI", "artificial intelligence"], "weight": 5},
                {"term": "Security", "aliases": ["security", "cybersecurity"], "weight": 6},
            ]
        }
        source = {"keywords": ["AI", "security", "new narrow signal"]}

        specs = monitor.keyword_specs(keywords_config, source)
        terms = [spec["term"] for spec in specs]

        self.assertEqual(terms.count("AI"), 1)
        self.assertEqual(terms.count("Security"), 1)
        self.assertIn("new narrow signal", terms)

    def test_mixed_classification_uses_default_mixed_action(self):
        finding = monitor.Finding(
            title="AI exploit with workflow gap",
            url="",
            source="Unit Test",
            source_type="manual_note",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="",
        )
        keywords_config = {"keywords": [{"term": "AI", "aliases": ["AI"], "weight": 1}]}
        rules = {
            "scoring": {"high_threshold": 999, "max_score": 100},
            "classification": {
                "risk_terms": ["exploit"],
                "opportunity_terms": ["workflow gap"],
            },
            "actions": {
                "default_mixed": "Mixed action",
                "default_risk": "Risk action",
                "default_opportunity": "Opportunity action",
                "default_observation": "Observation action",
            },
        }

        scored = monitor.score_finding(finding, {}, keywords_config, rules)

        self.assertEqual(scored.risk_or_opportunity, "mixed")
        self.assertEqual(scored.recommended_action, "Mixed action")

    def test_briefing_limits_items_per_source_per_section(self):
        def finding(title: str, source: str, score: int) -> monitor.Finding:
            return monitor.Finding(
                title=title,
                url="",
                source=source,
                source_type="rss",
                published_at=None,
                fetched_at="2026-01-01T00:00:00+00:00",
                summary="",
                relevance_score=score,
            )

        rules = {
            "scoring": {
                "high_threshold": 24,
                "medium_threshold": 12,
                "observe_threshold": 1,
            },
            "briefing": {
                "max_items_per_section": 3,
                "max_items_per_source_per_section": 1,
            },
        }

        markdown = monitor.render_briefing_md(
            [
                finding("A strongest", "Source A", 40),
                finding("A second", "Source A", 39),
                finding("A third", "Source A", 38),
                finding("B strongest", "Source B", 37),
            ],
            [],
            rules,
        )

        self.assertIn("A strongest", markdown)
        self.assertNotIn("A second", markdown)
        self.assertNotIn("A third", markdown)
        self.assertIn("B strongest", markdown)
        self.assertEqual(markdown.count("- Quelle: Source A"), 1)
        self.assertEqual(markdown.count("- Quelle: Source B"), 1)

    def test_watchgraph_caps_generic_github_repositories_below_high(self):
        rules = load_watchgraph_rules()
        finding = monitor.Finding(
            title="Awesome AI security automation privacy open source tutorial",
            url="https://github.com/example/awesome-ai-security",
            source="GitHub Search: AI Security Automation",
            source_type="github_search",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="Demo boilerplate repository for AI security automation privacy.",
        )
        source = {
            "type": "github_search",
            "mode": "repositories",
            "keywords": ["AI", "security", "automation", "privacy", "Open Source", "Produktidee"],
        }

        scored = monitor.score_finding(
            finding,
            source,
            yaml.safe_load((ROOT / "config" / "keywords.yaml").read_text(encoding="utf-8")),
            rules,
        )

        self.assertLess(scored.relevance_score, rules["scoring"]["high_threshold"])
        self.assertIn("watchgraph demote", scored.relevance_reason)
        self.assertIn("watchgraph confirmation gate", scored.relevance_reason)

    def test_watchgraph_allows_official_high_signal_disaster(self):
        rules = load_watchgraph_rules()
        finding = monitor.Finding(
            title="Earthquake tsunami warning and evacuation order near capital infrastructure",
            url="https://earthquake.usgs.gov/earthquakes/eventpage/example",
            source="USGS Significant Earthquakes",
            source_type="rss",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="PAGER and ShakeMap indicate possible infrastructure impact.",
        )
        source = {
            "id": "usgs_significant_earthquakes",
            "name": "USGS Significant Earthquakes",
            "type": "rss",
            "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.atom",
        }

        scored = monitor.score_finding(finding, source, {"keywords": []}, rules)

        self.assertGreaterEqual(scored.relevance_score, rules["scoring"]["high_threshold"])
        self.assertIn("Watchgraph:earthquakes_tsunami", scored.matched_keywords)
        self.assertIn("earthquakes_tsunami", scored.watchgraph_modules)
        self.assertIn("watchgraph high-signal", scored.relevance_reason)

    def test_watchgraph_uses_market_baskets_for_module_context(self):
        rules = load_watchgraph_rules()
        finding = monitor.Finding(
            title="AI agents and data center power context for NVDA and AVGO",
            url="https://openai.com/news/example",
            source="OpenAI News RSS",
            source_type="rss",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="Local-first memory workflows mention TSM and ASML supply constraints.",
        )
        source = {
            "id": "openai_news_rss",
            "name": "OpenAI News RSS",
            "type": "rss",
            "url": "https://openai.com/news/rss.xml",
        }

        scored = monitor.score_finding(finding, source, {"keywords": []}, rules)

        self.assertIn("Watchgraph:ai_agents_workflow", scored.matched_keywords)
        self.assertIn("ai_agents_workflow", scored.watchgraph_modules)
        self.assertIn("NVDA", scored.market_context)
        self.assertIn("watchgraph markets via", scored.relevance_reason)

    def test_watchgraph_demotes_generic_final_year_project_repo(self):
        finding = monitor.Finding(
            title="AI security automation final year project",
            url="https://github.com/example/final-year-ai-security",
            source="GitHub Search: AI Security Automation",
            source_type="github_search",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="It is my final year project for AI security automation privacy workflow.",
        )
        source = {"mode": "repositories", "keywords": ["AI", "security", "automation", "privacy"]}
        keywords_config = {
            "keywords": [
                {"term": "GitHub", "aliases": ["GitHub", "github.com"], "weight": 5},
                {"term": "AI", "aliases": ["AI"], "weight": 5},
                {"term": "Security", "aliases": ["security"], "weight": 6},
                {"term": "Automatisierung", "aliases": ["automation"], "weight": 5},
                {"term": "Datenschutz", "aliases": ["privacy"], "weight": 6},
            ]
        }
        rules = {
            "scoring": {"high_threshold": 24, "medium_threshold": 12, "observe_threshold": 1, "max_score": 100},
            "classification": {"risk_terms": ["security"], "opportunity_terms": ["automation"]},
            "watchgraph_scoring": {
                "demote_terms": ["final year project", "demo", "portfolio", "boilerplate"],
                "high_signal_boost_terms": ["actively exploited", "CISA KEV", "emergency patch"],
            },
            "actions": {
                "default_mixed": "Mixed action",
                "default_risk": "Risk action",
                "default_opportunity": "Opportunity action",
                "default_observation": "Observation action",
                "high_priority": "High action",
            },
        }

        scored = monitor.score_finding(finding, source, keywords_config, rules)

        self.assertLess(scored.relevance_score, 24)
        self.assertIn("watchgraph demote", scored.relevance_reason)

    def test_watchgraph_boosts_active_exploitation_signal(self):
        finding = monitor.Finding(
            title="CISA KEV actively exploited emergency patch for Ivanti",
            url="https://example.com/security/advisory",
            source="CISA Cybersecurity Advisories",
            source_type="rss",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="A vulnerability is actively exploited in the wild and requires emergency patching.",
        )
        source = {"keywords": ["CISA", "CVE", "vulnerability"]}
        keywords_config = {
            "keywords": [
                {"term": "Security", "aliases": ["security", "vulnerability"], "weight": 6},
                {"term": "CISA", "aliases": ["CISA"], "weight": 8},
            ]
        }
        rules = {
            "scoring": {"high_threshold": 24, "medium_threshold": 12, "observe_threshold": 1, "max_score": 100},
            "classification": {"risk_terms": ["vulnerability", "actively exploited"], "opportunity_terms": []},
            "watchgraph_scoring": {
                "demote_terms": ["demo", "final year project"],
                "high_signal_boost_terms": ["actively exploited", "CISA KEV", "emergency patch"],
            },
            "actions": {
                "default_risk": "Risk action",
                "default_observation": "Observation action",
                "high_priority": "High action",
                "watchgraph_hot": "Watchgraph hot action",
            },
        }

        scored = monitor.score_finding(finding, source, keywords_config, rules)

        self.assertGreaterEqual(scored.relevance_score, 24)
        self.assertIn("watchgraph high-signal", scored.relevance_reason)
        self.assertIn("Watchgraph hot action", scored.recommended_action)

    def test_runtime_governance_binds_finance_terms_and_official_classes(self):
        rules = monitor.load_runtime_rules()
        watchgraph_rules = rules["watchgraph_scoring"]

        self.assertIn("emergency rate", watchgraph_rules["high_signal_boost_terms"])
        self.assertIn("margin call", watchgraph_rules["financial_signal_terms"])
        self.assertEqual(watchgraph_rules["financial_signal_bonus"]["max_points"], 8.0)
        self.assertIn("central_bank_network", watchgraph_rules["official_source_classes"])
        self.assertIn("market_operator", watchgraph_rules["official_source_classes"])

    def test_financial_context_bonus_is_bounded_without_high_priority_bypass(self):
        rules = monitor.load_runtime_rules()
        finding = monitor.Finding(
            title="Margin call, liquidity squeeze and repo spike",
            url="https://example.test/market",
            source="Specialist market report",
            source_type="rss",
            published_at=None,
            fetched_at="2026-08-28T00:00:00+00:00",
            summary="Funding stress and deposit outflow are reported.",
        )

        scored = monitor.score_finding(finding, {}, {"keywords": []}, rules)

        self.assertEqual(scored.relevance_score, 8)
        self.assertIn("financial-market signal", scored.relevance_reason)
        self.assertLess(scored.relevance_score, rules["scoring"]["high_threshold"])

    def test_watchgraph_modules_and_market_context_are_attached(self):
        finding = monitor.Finding(
            title="Major earthquake triggers tsunami warning",
            url="https://example.com/quake",
            source="USGS Significant Earthquakes",
            source_type="rss",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="Earthquake aftershock and tsunami warning near critical infrastructure.",
        )
        source = {"keywords": ["earthquake", "tsunami warning"]}
        keywords_config = {
            "keywords": [
                {"term": "Earthquake", "aliases": ["earthquake"], "weight": 6},
                {"term": "Tsunami", "aliases": ["tsunami warning"], "weight": 8},
            ]
        }
        rules = {
            "scoring": {"high_threshold": 24, "medium_threshold": 12, "observe_threshold": 1, "max_score": 100},
            "classification": {"risk_terms": ["earthquake", "tsunami warning"], "opportunity_terms": []},
            "watchgraph_scoring": {
                "demote_terms": [],
                "high_signal_boost_terms": ["tsunami warning"],
            },
            "actions": {
                "default_risk": "Risk action",
                "watchgraph_hot": "Watchgraph hot action",
                "high_priority": "High action",
            },
        }
        watchgraph = {
            "modules": [
                {
                    "id": "earthquakes_tsunami",
                    "buzzwords": ["earthquake", "aftershock", "tsunami warning"],
                    "market_basket": ["MUV2.DE", "SREN.SW"],
                }
            ]
        }

        scored = monitor.score_finding(finding, source, keywords_config, rules, watchgraph, {})

        self.assertIn("earthquakes_tsunami", scored.watchgraph_modules)
        self.assertIn("MUV2.DE", scored.market_context)
        self.assertIn("watchgraph modules", scored.relevance_reason)

    def test_single_generic_github_repo_is_capped_below_high(self):
        finding = monitor.Finding(
            title="AI security privacy automation framework",
            url="https://github.com/example/random-ai-security",
            source="GitHub Search: AI Security Automation",
            source_type="github_search",
            published_at=None,
            fetched_at="2026-01-01T00:00:00+00:00",
            summary="AI security privacy automation GitHub repository for workflow automation.",
        )
        source = {"mode": "repositories", "keywords": ["AI", "security", "automation", "privacy"]}
        keywords_config = {
            "keywords": [
                {"term": "GitHub", "aliases": ["GitHub", "github.com"], "weight": 5},
                {"term": "AI", "aliases": ["AI"], "weight": 7},
                {"term": "Security", "aliases": ["security"], "weight": 8},
                {"term": "Automatisierung", "aliases": ["automation"], "weight": 7},
                {"term": "Datenschutz", "aliases": ["privacy"], "weight": 7},
            ]
        }
        rules = {
            "scoring": {"high_threshold": 24, "medium_threshold": 12, "observe_threshold": 1, "max_score": 100},
            "classification": {"risk_terms": ["security"], "opportunity_terms": ["automation"]},
            "watchgraph_scoring": {
                "demote_terms": [],
                "high_signal_boost_terms": ["actively exploited", "CISA KEV", "emergency patch"],
            },
            "actions": {
                "default_mixed": "Mixed action",
                "default_risk": "Risk action",
                "default_opportunity": "Opportunity action",
                "default_observation": "Observation action",
                "high_priority": "High action",
            },
        }

        scored = monitor.score_finding(finding, source, keywords_config, rules)

        self.assertLess(scored.relevance_score, 24)
        self.assertIn("single GitHub repository description requires confirmation", scored.relevance_reason)

    def test_archived_and_forked_repository_results_are_skipped(self):
        self.assertTrue(monitor.should_skip_repository_result({"archived": True, "fork": False}))
        self.assertTrue(monitor.should_skip_repository_result({"archived": False, "fork": True}))
        self.assertFalse(monitor.should_skip_repository_result({"archived": False, "fork": False}))


class MonitorConfigTests(unittest.TestCase):
    def test_rules_yaml_exposes_mixed_action_and_source_render_limit(self):
        rules = yaml.safe_load((ROOT / "config" / "rules.yaml").read_text(encoding="utf-8"))

        self.assertIn("default_mixed", rules["actions"])
        self.assertGreaterEqual(rules["scoring"]["high_threshold"], 24)
        self.assertGreaterEqual(rules["scoring"]["medium_threshold"], 12)
        self.assertGreaterEqual(rules["briefing"]["max_items_per_source_per_section"], 1)


if __name__ == "__main__":
    unittest.main()
