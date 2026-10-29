"""
test_product_profile.py
───────────────────────
Unit and integration tests for ProductProfile extraction and post-validation.
Verifies Phase 3 acceptance criteria:
1. Valid ProductProfile produced matching schema.
2. Fixture with no price lists 'price' in missing_data and has no price in proof_points.
3. Hallucinated visual assets are stripped by post-validation.
4. Un-grounded proof points are dropped.
"""

import os
import sys
import json
import unittest
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv

# Ensure environment is loaded from .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from tools.video_pipeline.schemas import ProductProfile, ProofPoint, ToneEnum
from tools.video_pipeline.product_profile import (
    post_validate_profile,
    build_crawl_digest,
    extract_product_profile
)


class TestProductProfile(unittest.TestCase):

    def test_post_validation_strips_hallucinated_assets(self):
        """Hallucinated visual assets that do not exist on disk are stripped."""
        profile = ProductProfile(
            name="TestApp",
            what_it_is="A modern testing tool",
            audience="Developers",
            core_differentiator="Lightning fast test runs",
            tone=ToneEnum.technical,
            category="developer_tools",
            visual_style_hint="dark minimal",
            proof_points=[ProofPoint(text="10x faster execution", source="hero")],
            visual_assets_available=["real_logo.png", "hallucinated_screenshot.png", "fake_mockup.svg"],
            missing_data=["price"],
            language="en"
        )

        disk_assets = ["real_logo.png"]
        ground_truth = {"price": False, "rating": False, "logo": True, "product_image": True}
        raw_corpus = "TestApp A modern testing tool 10x faster execution"

        validated = post_validate_profile(profile, disk_assets, raw_corpus, ground_truth)

        # Only real_logo.png should remain
        self.assertEqual(validated.visual_assets_available, ["real_logo.png"])

    def test_missing_price_enforcement(self):
        """A product with no extracted price lists 'price' in missing_data and has no price in proof_points."""
        profile = ProductProfile(
            name="TestApp",
            what_it_is="Cloud platform",
            audience="Startups",
            core_differentiator="Zero setup deploy",
            tone=ToneEnum.urgent,
            category="saas",
            visual_style_hint="bold gradient",
            proof_points=[
                ProofPoint(text="Starting at only ₹1,499 per month", source="pricing"),  # Hallucinated price!
                ProofPoint(text="Zero setup deploy guaranteed", source="hero")
            ],
            visual_assets_available=[],
            missing_data=[],  # Model omitted price from missing_data!
            language="en"
        )

        disk_assets = []
        ground_truth = {"price": False, "rating": False, "logo": False, "product_image": False}
        raw_corpus = "TestApp Cloud platform Zero setup deploy guaranteed"

        validated = post_validate_profile(profile, disk_assets, raw_corpus, ground_truth)

        # Price must be in missing_data
        self.assertIn("price", validated.missing_data)
        self.assertIn("rating", validated.missing_data)

        # Hallucinated price proof point must be dropped
        proof_texts = [p.text for p in validated.proof_points]
        self.assertNotIn("Starting at only ₹1,499 per month", proof_texts)
        self.assertIn("Zero setup deploy guaranteed", proof_texts)

    def test_mock_product_profile_extraction(self):
        """Runs extract_product_profile in mock mode."""
        os.environ["DIRECTOR_MOCK"] = "1"
        try:
            brand_data = {
                "name": "Acme Cloud",
                "domain": "acme.dev",
                "tagline": "Serverless cloud runtime for modern developers",
                "description": "Sub-millisecond cold starts with zero configuration",
                "products": ["Edge Compute", "Serverless DB"]
            }
            ui_desc = {
                "price_info": None,
                "rating": None,
                "trust_badges": ["SOC2 Certified"],
                "brand_distinguishers": ["Global Edge Network"]
            }

            profile = extract_product_profile(
                brand_data=brand_data,
                ui_desc=ui_desc,
                run_id="test_mock_profile"
            )

            self.assertIsInstance(profile, ProductProfile)
            self.assertEqual(profile.name, "Acme Cloud")
            self.assertIn("price", profile.missing_data)
            self.assertIn(profile.tone, list(ToneEnum))
        finally:
            os.environ.pop("DIRECTOR_MOCK", None)

    def test_flipkart_job_profile_extraction(self):
        """Runs profile extraction on actual flipkart-001 job data."""
        job_dir = Path("remotion/jobs/flipkart-001")
        if not job_dir.exists():
            self.skipTest("flipkart-001 job not found")

        with open(job_dir / "brand.json", "r", encoding="utf-8") as f:
            brand_data = json.load(f)

        ui_desc = None
        if (job_dir / "ui_description.json").exists():
            with open(job_dir / "ui_description.json", "r", encoding="utf-8") as f:
                ui_desc = json.load(f)

        profile = extract_product_profile(
            brand_data=brand_data,
            ui_desc=ui_desc,
            assets_dir=job_dir / "assets",
            run_id="flipkart_test"
        )

        self.assertIsInstance(profile, ProductProfile)
        self.assertEqual(profile.name.lower(), "flipkart")
        self.assertIn("price", profile.missing_data)
        # Verify visual assets genuinely exist in assets dir
        for asset in profile.visual_assets_available:
            self.assertTrue((job_dir / "assets" / asset).exists())


if __name__ == "__main__":
    unittest.main()
