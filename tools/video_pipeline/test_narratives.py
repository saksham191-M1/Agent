"""
test_narratives.py
──────────────────
Unit tests for Narrative Arc loading, schema validation, and intelligent selection.
Verifies Phase 4 acceptance criteria:
1. narratives.json loads and strictly matches NarrativeArc schema.
2. Narrative selection matches appropriate product tones and categories.
3. No-fake-data constraint: pricing arcs are avoided when price is in missing_data.
4. Global rules verification: all arcs have scene counts in [3, 8] and durations in [10, 40]s.
"""

import unittest
from pathlib import Path

from tools.video_pipeline.schemas import (
    NarrativeArc,
    ProductProfile,
    ProofPoint,
    ToneEnum
)
from tools.video_pipeline.narratives import (
    load_narratives,
    select_narrative,
    score_narrative_match
)


class TestNarratives(unittest.TestCase):

    def test_load_narratives_schema(self):
        """Validates all arcs in narratives.json match NarrativeArc schema."""
        arcs = load_narratives()
        self.assertGreaterEqual(len(arcs), 5)
        for arc in arcs:
            self.assertIsInstance(arc, NarrativeArc)
            self.assertTrue(len(arc.id) > 0)
            self.assertTrue(len(arc.scene_blueprints) >= 3)

    def test_global_pipeline_bounds(self):
        """Global rule: scene counts in [3, 8], total durations in [10, 40] seconds."""
        arcs = load_narratives()
        for arc in arcs:
            min_scenes, max_scenes = arc.scene_count_range
            min_sec, max_sec = arc.duration_seconds_range
            self.assertGreaterEqual(min_scenes, 3, f"{arc.id} min_scenes < 3")
            self.assertLessEqual(max_scenes, 8, f"{arc.id} max_scenes > 8")
            self.assertGreaterEqual(min_sec, 10.0, f"{arc.id} min_duration < 10s")
            self.assertLessEqual(max_sec, 40.0, f"{arc.id} max_duration > 40s")

    def test_select_dev_tool(self):
        """Technical developer tool selects technical_deep_dive."""
        profile = ProductProfile(
            name="Supabase",
            what_it_is="The open source Firebase alternative",
            audience="Fullstack and backend developers",
            core_differentiator="Postgres with instant realtime APIs",
            tone=ToneEnum.technical,
            category="dev_tool",
            visual_style_hint="dark minimal",
            proof_points=[ProofPoint(text="100,000 active databases", source="homepage")],
            visual_assets_available=["logo.svg"],
            missing_data=["price"],
            language="en"
        )
        selected = select_narrative(profile)
        self.assertEqual(selected.id, "technical_deep_dive")

    def test_select_b2b_saas(self):
        """B2B SaaS product with premium tone selects saas_workflow_reveal."""
        profile = ProductProfile(
            name="Linear",
            what_it_is="Issue tracking software built for high-performance product teams",
            audience="Product managers and engineering leads",
            core_differentiator="Sub-50ms interaction latency with keyboard shortcuts",
            tone=ToneEnum.premium,
            category="web_saas",
            visual_style_hint="dark sleek glass",
            proof_points=[ProofPoint(text="Zero-latency sync engine", source="hero")],
            visual_assets_available=["studio-hero.png"],
            missing_data=["price"],
            language="en"
        )
        selected = select_narrative(profile)
        self.assertEqual(selected.id, "saas_workflow_reveal")

    def test_select_ecommerce_with_price(self):
        """Ecommerce with extracted price selects urgent_deal_drop."""
        profile = ProductProfile(
            name="Flipkart",
            what_it_is="Online shopping destination with millions of products",
            audience="Shoppers looking for unbeatable discounts",
            core_differentiator="Lowest guaranteed price with Assured doorstep delivery",
            tone=ToneEnum.urgent,
            category="ecommerce",
            visual_style_hint="energetic blue and yellow high-contrast",
            proof_points=[ProofPoint(text="Up to 70% off on electronics", source="banner")],
            visual_assets_available=["studio-hero.png", "studio-mobile.png"],
            missing_data=[],  # Price is present
            language="en"
        )
        selected = select_narrative(profile)
        self.assertEqual(selected.id, "urgent_deal_drop")

    def test_ecommerce_missing_price_avoids_pricing_arc(self):
        """When price is missing from crawl, pricing-centric arcs are penalized and avoided."""
        profile = ProductProfile(
            name="MysteryStore",
            what_it_is="Online boutique",
            audience="Boutique shoppers",
            core_differentiator="Curated collection",
            tone=ToneEnum.urgent,
            category="ecommerce",
            visual_style_hint="minimal luxury",
            proof_points=[],
            visual_assets_available=[],
            missing_data=["price"],  # Price was missing!
            language="en"
        )
        selected = select_narrative(profile)
        # Must NOT select urgent_deal_drop because that requires pricing
        self.assertNotEqual(selected.id, "urgent_deal_drop")
        # Should fall back to problem_agitate_solution or general arc
        self.assertIn(selected.id, ["problem_agitate_solution", "minimal_aesthetic_reveal"])


if __name__ == "__main__":
    unittest.main()
