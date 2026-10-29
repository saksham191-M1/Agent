import unittest
from tools.video_pipeline.schemas import ProductProfile, StoryboardDirectorSpec, SceneDirectorSpec, ProofPoint, ToneEnum
from tools.video_pipeline.storyboard_validator import validate_storyboard

class TestStoryboardValidator(unittest.TestCase):
    def setUp(self):
        self.profile = ProductProfile(
            name="Zomato",
            category="consumer",
            what_it_is="Online food delivery and restaurant discovery",
            audience="Food lovers",
            core_differentiator="Fast reliable doorstep meal delivery",
            tone=ToneEnum.playful,
            visual_style_hint="bright red appetizing food photography",
            proof_points=[
                ProofPoint(text="Over 300,000 restaurant partners", source="annual_report")
            ],
            visual_assets_available=[]
        )

    def test_catches_foreign_brand(self):
        bad_storyboard = StoryboardDirectorSpec(
            product_name="Zomato",
            narrative_type="speed_efficiency",
            total_seconds=12.0,
            scene_count=3,
            music_mood="energetic_pop",
            voice_style="energetic",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    motion_profile="snappy",
                    voiceover="Tired of waiting for dinner?",
                    kinetic_text="CRAVING GOOD FOOD",
                    visual_fx="fast_zoom"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="phone",
                    motion_profile="smooth",
                    voiceover="Order on Swiggy for quick bites.", # Foreign brand!
                    kinetic_text="ORDER INSTANTLY",
                    visual_fx="pan_right"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    motion_profile="snappy",
                    voiceover="Eat what you love.",
                    kinetic_text="DISCOVER TODAY",
                    visual_fx="fade_in"
                )
            ]
        )
        valid, errors = validate_storyboard(self.profile, bad_storyboard)
        self.assertFalse(valid)
        self.assertTrue(any("foreign brand 'swiggy'" in e for e in errors))

    def test_catches_unsupported_numbers(self):
        bad_numbers_storyboard = StoryboardDirectorSpec(
            product_name="Zomato",
            narrative_type="speed_efficiency",
            total_seconds=12.0,
            scene_count=3,
            music_mood="energetic_pop",
            voice_style="energetic",
            scenes=[
                SceneDirectorSpec(
                    scene_id=1,
                    duration_seconds=4.0,
                    layout="hero-type",
                    motion_profile="snappy",
                    voiceover="Three billion orders delivered.", # Unsupported 'billion'!
                    kinetic_text="THREE BILLION ORDERS",
                    visual_fx="fast_zoom"
                ),
                SceneDirectorSpec(
                    scene_id=2,
                    duration_seconds=4.0,
                    layout="phone",
                    motion_profile="smooth",
                    voiceover="Browse menus near you.",
                    kinetic_text="EXPLORE RESTAURANTS",
                    visual_fx="pan_right"
                ),
                SceneDirectorSpec(
                    scene_id=3,
                    duration_seconds=4.0,
                    layout="cta",
                    motion_profile="snappy",
                    voiceover="Order now.",
                    kinetic_text="GET STARTED",
                    visual_fx="fade_in"
                )
            ]
        )
        valid, errors = validate_storyboard(self.profile, bad_numbers_storyboard)
        self.assertFalse(valid)
        self.assertTrue(any("billion" in e for e in errors))

if __name__ == '__main__':
    unittest.main()
