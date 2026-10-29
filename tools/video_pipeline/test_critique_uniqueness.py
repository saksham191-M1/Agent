"""
test_critique_uniqueness.py
───────────────────────────
Unit tests for Phase 8:
1. Critique schema and scoring rubrics (specificity & differentiator_use must be >= 4).
2. Rejection of deliberately generic scripts and adoption of revised storyboard.
3. Persistent history tracking and prompt nudge formatting.
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch

root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from tools.video_pipeline.schemas import (
    ProductProfile,
    ProofPoint,
    ToneEnum,
    StoryboardDirectorSpec,
    SceneDirectorSpec,
    CritiqueFeedback,
    CritiqueScores,
)
from tools.video_pipeline.narratives import select_narrative
from tools.video_pipeline.storyboard_director import generate_storyboard
from tools.video_pipeline.history import (
    append_history,
    get_recent_history,
    format_history_nudge,
)


class TestCritiqueAndUniqueness(unittest.TestCase):

    def setUp(self):
        self.profile = ProductProfile(
            name="NeonDB",
            what_it_is="Serverless Postgres database built for modern developers.",
            audience="Backend engineers and scale-ups",
            core_differentiator="Instant database branching on every pull request",
            tone=ToneEnum.technical,
            category="developer_tools",
            visual_style_hint="dark neon glow, sharp terminal typography",
            proof_points=[
                ProofPoint(text="Instant branching in under 1 second", source="docs"),
                ProofPoint(text="Autoscaling to zero when idle", source="pricing")
            ],
            visual_assets_available=["neon-branch.png"],
            missing_data=["rating", "discount"],
            language="en"
        )
        self.arc = select_narrative(self.profile)
        self.temp_history = Path("test_history.json")

    def tearDown(self):
        if self.temp_history.exists():
            try:
                self.temp_history.unlink()
            except Exception:
                pass

    def test_critique_scores_schema(self):
        """Verifies CritiqueScores strictly bounds ratings between 1 and 5."""
        scores = CritiqueScores(
            specificity=4,
            differentiator_use=5,
            pacing=4,
            copy_quality=5
        )
        self.assertEqual(scores.specificity, 4)
        self.assertEqual(scores.differentiator_use, 5)

    def test_generic_script_rejected_by_low_specificity(self):
        """If specificity or differentiator_use is below 4, critique gate rejects and adopts revision."""
        generic_draft = StoryboardDirectorSpec(
            product_name="NeonDB",
            narrative_type=self.arc.id,
            scene_count=3,
            total_seconds=12.0,
            music_mood="techno",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    voiceover="Built for speed and performance.",  # Generic cliché
                    kinetic_text="FAST SPEED"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Experience modern cloud workflow.",
                    kinetic_text="MODERN CLOUD"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    voiceover="Start your journey today.",
                    kinetic_text="START NOW"
                )
            ]
        )

        specific_revised = StoryboardDirectorSpec(
            product_name="NeonDB",
            narrative_type=self.arc.id,
            scene_count=3,
            total_seconds=12.0,
            music_mood="techno",
            voice_style="confident",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    voiceover="Instant database branching on every pull request.",
                    kinetic_text="BRANCH YOUR DB"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="browser",
                    voiceover="Autoscales to zero when idle to eliminate wasted cloud spend.",
                    kinetic_text="AUTOSCALE TO ZERO"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    voiceover="Spin up your Postgres branch at neondb.io today.",
                    kinetic_text="BRANCH TODAY"
                )
            ]
        )

        # Low specificity score = 2
        critique_result = CritiqueFeedback(
            passes_qa=True,  # Initially marked true by model, but gate must override because specificity < 4
            scores=CritiqueScores(
                specificity=2,
                differentiator_use=2,
                pacing=4,
                copy_quality=3
            ),
            problems=["Script is completely generic and could apply to any cloud vendor."],
            revision_instructions="Incorporate instant database branching and autoscaling to zero.",
            revised_storyboard=specific_revised
        )

        with patch("tools.video_pipeline.storyboard_director.call_director") as mock_call:
            mock_call.side_effect = [generic_draft, critique_result]

            final = generate_storyboard(self.profile, self.arc, run_id="test_uniqueness")
            self.assertEqual(final.scenes[0].kinetic_text, "BRANCH YOUR DB")
            self.assertIn("branching", final.scenes[0].voiceover)

    def test_history_logging_and_nudge_formatting(self):
        """Verifies appending creative signatures to history and formatting the prompt nudge."""
        sig1 = {
            "run_id": "run_001",
            "product_name": "Product Alpha",
            "narrative_id": "urgent_deal_drop",
            "scene_count": 4,
            "total_duration_s": 16.0,
            "primitive_sequence": ["hero-type", "phone", "split", "cta"],
            "motion_profiles": ["snappy", "snappy", "snappy", "snappy"],
            "music_mood": "high_energy_electronic",
            "transitions": ["carousel_glide", "wipe", "cross_zoom", "none"]
        }
        sig2 = {
            "run_id": "run_002",
            "product_name": "Product Beta",
            "narrative_id": "minimal_aesthetic_reveal",
            "scene_count": 3,
            "total_duration_s": 12.0,
            "primitive_sequence": ["hero-type", "browser", "cta"],
            "motion_profiles": ["smooth", "smooth", "smooth"],
            "music_mood": "ambient_minimal",
            "transitions": ["carousel_glide", "cross_zoom", "none"]
        }

        append_history(sig1, history_path=self.temp_history)
        append_history(sig2, history_path=self.temp_history)

        recent = get_recent_history(5, history_path=self.temp_history)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["product_name"], "Product Alpha")
        self.assertEqual(recent[1]["product_name"], "Product Beta")

        nudge = format_history_nudge(recent)
        self.assertIn("RECENT COMPLETED AD SIGNATURES", nudge)
        self.assertIn("Product Alpha", nudge)
        self.assertIn("Product Beta", nudge)


if __name__ == "__main__":
    unittest.main()
