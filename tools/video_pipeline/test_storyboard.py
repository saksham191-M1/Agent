"""
test_storyboard.py
──────────────────
Unit and integration tests for Phase 5:
- Storyboard generation via Director AI Gateway
- Critique & revision gate
- Code-level deterministic sanitization (terminal punctuation ban, exact duration sum, sequential scene IDs)
"""

import os
import sys
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import unittest
from unittest.mock import patch, MagicMock

from tools.video_pipeline.schemas import (
    ProductProfile,
    ProofPoint,
    ToneEnum,
    NarrativeArc,
    SceneBlueprint,
    StoryboardDirectorSpec,
    SceneDirectorSpec,
    CritiqueFeedback,
)
from tools.video_pipeline.narratives import select_narrative
from tools.video_pipeline.storyboard_director import (
    generate_storyboard,
    sanitize_storyboard,
    load_storyboard_prompt,
    load_critique_prompt,
)


class TestStoryboardDirector(unittest.TestCase):

    def setUp(self):
        self.profile = ProductProfile(
            name="Supabase",
            what_it_is="The open source Firebase alternative with Postgres database, auth, and storage.",
            audience="Software engineers and founders",
            core_differentiator="Full Postgres backend ready in under 2 minutes",
            tone=ToneEnum.technical,
            category="developer_tools",
            visual_style_hint="dark mode, emerald green accents, monospace code",
            proof_points=[
                ProofPoint(text="100k+ active databases", source="landing page"),
                ProofPoint(text="Postgres under the hood", source="docs")
            ],
            visual_assets_available=["supabase-hero.png"],
            missing_data=["price", "discount", "rating"],
            language="en"
        )
        self.arc = select_narrative(self.profile)

    def test_prompts_exist_and_load(self):
        sb_prompt = load_storyboard_prompt()
        self.assertIn("Creative Director", sb_prompt)
        self.assertIn("BAN TERMINAL PUNCTUATION", sb_prompt)

        crit_prompt = load_critique_prompt()
        self.assertIn("Critique", crit_prompt)
        self.assertIn("INVENTED FACTS CHECK", crit_prompt)

    def test_deterministic_sanitization_strips_punctuation(self):
        """Headlines must never end with terminal punctuation (., :, ;, !, ?)."""
        dirty_spec = StoryboardDirectorSpec(
            product_name="TestApp",
            narrative_type="test_arc",
            scene_count=3,
            total_seconds=25.0,  # Deliberately mismatched from scene sum (11.0)
            music_mood="upbeat",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=10,
                    duration_seconds=3.5,
                    layout="hero-type",
                    voiceover="Welcome to the app.",
                    kinetic_text="START NOW."  # Terminal period
                ),
                SceneDirectorSpec(
                    scene_id=20,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Watch the workflow.",
                    kinetic_text="EXPLORE:"  # Terminal colon
                ),
                SceneDirectorSpec(
                    scene_id=30,
                    duration_seconds=3.5,
                    layout="cta",
                    voiceover="Try it for free.",
                    kinetic_text="GET STARTED!"  # Terminal exclamation
                )
            ]
        )

        clean = sanitize_storyboard(dirty_spec, arc=self.arc, profile=self.profile)

        # 1. Terminal punctuation stripped
        self.assertEqual(clean.scenes[0].kinetic_text, "START NOW")
        self.assertEqual(clean.scenes[1].kinetic_text, "EXPLORE")
        self.assertEqual(clean.scenes[2].kinetic_text, "GET STARTED")

        # 2. Sequential scene IDs
        self.assertEqual([s.scene_id for s in clean.scenes], [1, 2, 3])

        # 3. Exact duration sum (3.5 + 4.0 + 3.5 = 11.0)
        self.assertEqual(clean.total_seconds, 11.0)
        self.assertEqual(clean.scene_count, 3)

        # 4. Identity metadata filled
        self.assertEqual(clean.product_name, "Supabase")
        self.assertEqual(clean.narrative_type, self.arc.id)
        self.assertEqual(clean.selected_template, self.arc.name)

    @patch.dict(os.environ, {"DIRECTOR_MOCK": "1"})
    def test_generate_storyboard_mock_flow(self):
        """Verifies end-to-end storyboard generation with mock Director AI."""
        storyboard = generate_storyboard(self.profile, self.arc, run_id="test_run_mock")
        self.assertIsInstance(storyboard, StoryboardDirectorSpec)
        self.assertGreaterEqual(len(storyboard.scenes), 3)
        self.assertEqual(storyboard.total_seconds, round(sum(s.duration_seconds for s in storyboard.scenes), 2))
        for scene in storyboard.scenes:
            self.assertFalse(scene.kinetic_text.endswith("."))
            self.assertFalse(scene.kinetic_text.endswith(":"))
            self.assertFalse(scene.kinetic_text.endswith(";"))

    def test_critique_gate_adopts_revision_on_failure(self):
        """If Critique flags invented facts or punctuation and supplies revision, revision is adopted."""
        draft = StoryboardDirectorSpec(
            product_name="Supabase",
            narrative_type=self.arc.id,
            scene_count=3,
            total_seconds=12.0,
            music_mood="electronic",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    voiceover="Only 99 dollars a month.",  # Fake price
                    kinetic_text="LOW PRICE."
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Rated 5 stars by all users.",  # Fake rating
                    kinetic_text="5 STARS."
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    voiceover="Try it today.",
                    kinetic_text="SHIP TODAY."
                )
            ]
        )

        corrected = StoryboardDirectorSpec(
            product_name="Supabase",
            narrative_type=self.arc.id,
            scene_count=3,
            total_seconds=12.0,
            music_mood="electronic",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    voiceover="The open source Firebase alternative with Postgres.",
                    kinetic_text="OPEN SOURCE"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Postgres backend ready in under 2 minutes.",
                    kinetic_text="INSTANT POSTGRES"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    voiceover="Start building at supabase.com today.",
                    kinetic_text="SHIP TODAY"
                )
            ]
        )

        critique_result = CritiqueFeedback(
            passes_qa=False,
            invented_facts_detected=["Fake $99 price in scene 1", "Fake 5 stars rating in scene 2"],
            punctuation_violations=["LOW PRICE.", "5 STARS.", "SHIP TODAY."],
            revision_notes="Replaced hallucinated price and ratings with verified Postgres features.",
            revised_storyboard=corrected
        )

        with patch("tools.video_pipeline.storyboard_director.call_director") as mock_call:
            mock_call.side_effect = [draft, critique_result]

            final = generate_storyboard(self.profile, self.arc, run_id="test_critique")
            self.assertEqual(final.scenes[0].kinetic_text, "OPEN SOURCE")
            self.assertIn("Postgres", final.scenes[0].voiceover)

    def test_critique_gate_graceful_on_error(self):
        """If Critique call fails or raises exception, the sanitized draft is safely retained."""
        draft = StoryboardDirectorSpec(
            product_name="Supabase",
            narrative_type=self.arc.id,
            scene_count=3,
            total_seconds=12.0,
            music_mood="electronic",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    voiceover="The open source Firebase alternative.",
                    kinetic_text="OPEN SOURCE"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Instant Postgres databases.",
                    kinetic_text="POSTGRES"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    voiceover="Get started today.",
                    kinetic_text="START TODAY"
                )
            ]
        )

        with patch("tools.video_pipeline.storyboard_director.call_director") as mock_call:
            mock_call.side_effect = [draft, Exception("Critique timeout")]

            final = generate_storyboard(self.profile, self.arc, run_id="test_critique_err")
            self.assertEqual(final.scenes[0].kinetic_text, "OPEN SOURCE")
            self.assertEqual(len(final.scenes), 3)


if __name__ == "__main__":
    unittest.main()
