import unittest
import tempfile
from pathlib import Path
from jarvis.ai_content.scripts.compositors.ecproj_builder import build_ecproj, Ecproj
from jarvis.ai_content.scripts.providers.gemini_provider import GeminiProvider
from jarvis.ai_content.scripts.providers.omni_provider import OmniProvider
from jarvis.ai_content.scripts.video.google_flow_automation import GoogleFlowAutomation
from jarvis.ai_content.scripts.validators.contract_validator import (
    validate_visual_contract,
    validate_storyboard,
    validate_generated_clip
)
from jarvis.ai_content.scripts.audio.sfx_beat_engine import SFXBeatEngine
from jarvis.ai_content.scripts.audio.audio_mixer import AudioMixer, ProceduralSFXSynthesizer
from jarvis.ai_content.scripts.metrics.tracker import RunTracker
from jarvis.ai_content.scripts.pipeline import run_pipeline


class TestAIContentPipeline(unittest.TestCase):
    def test_ecproj_model_validate(self):
        mock_scene = {
            "scene_id": "test_01",
            "duration": 4.0,
            "purpose": "Hook_Problem",
            "title": "Automate Everything",
            "subtitle": "Faster workflows",
            "primary_color": "#6366F1",
            "secondary_color": "#0A0A12",
            "color_grade": "teal_orange_cinematic",
            "needs_particles": False
        }
        proj = build_ecproj(mock_scene, Path("dummy_clip.mp4"))
        self.assertIsInstance(proj, Ecproj)
        self.assertEqual(len(proj.layers), 4)
        self.assertEqual(proj.composition["duration"], 4.0)
        self.assertEqual(proj.composition["width"], 1920)

    def test_visual_contract_validation_and_entity_continuity(self):
        valid_raw = {
            "script_id": "bottle_cap_01",
            "total_duration": 10.0,
            "tts_script_with_breaks": "Can anyone pull this off? <break time=\"400ms\"/> Watch closely.",
            "tts_tone": "energetic",
            "music_genre": "uplifting_future_bass",
            "energy_curve": "slow_build_to_fast",
            "entities": [
                {"id": "char_athlete", "type": "character", "description": "athlete in black training gear"},
                {"id": "item_bottle", "type": "object", "description": "transparent glass water bottle"}
            ],
            "scenes_outline": [
                {
                    "scene_id": "01",
                    "purpose": "Hook_Problem",
                    "duration": 5.0,
                    "voiceover_line": "Can anyone pull this off? <break time=\"400ms\"/>",
                    "entity_refs": ["char_athlete", "item_bottle"],
                    "visual_elements": {
                        "characters": ["athlete in black training gear"],
                        "key_items": ["transparent glass water bottle"],
                        "core_action": "athlete performs a spinning kick beside the bottle",
                        "visual_setting": "neon-lit gym at night",
                        "camera_move": {
                            "shot_type": "medium_wide",
                            "movement": "tracking_dolly",
                            "speed": "slow_motion",
                            "focus": "athlete and bottle"
                        }
                    },
                    "constraints": {
                        "must_preserve": ["transparent glass bottle", "one athlete", "neon-lit gym"],
                        "must_not_include": ["additional people", "plastic bottle", "outdoor park"]
                    }
                },
                {
                    "scene_id": "02",
                    "purpose": "CTA",
                    "duration": 5.0,
                    "voiceover_line": "Watch closely and try the challenge.",
                    "entity_refs": ["item_bottle"],
                    "visual_elements": {
                        "characters": [],
                        "key_items": ["transparent glass water bottle"],
                        "core_action": "bottle cap spins off into the air as bottle stays still",
                        "visual_setting": "neon-lit gym at night"
                    }
                }
            ]
        }
        res = validate_visual_contract(valid_raw)
        self.assertTrue(res.valid, f"Expected valid contract, got errors: {res.errors}")
        self.assertEqual(len(res.data.entities), 2)

        # Invalid entity reference must hard-fail
        invalid_raw = dict(valid_raw)
        invalid_raw["scenes"] = [
            {
                **valid_raw["scenes"][0],
                "entity_refs": ["unknown_ghost_id"]
            },
            valid_raw["scenes"][1]
        ]
        bad_res = validate_visual_contract(invalid_raw)
        self.assertFalse(bad_res.valid)
        self.assertTrue(any("unknown entity" in e for e in bad_res.errors))

    def test_sfx_beat_engine_action_mapping(self):
        engine = SFXBeatEngine()
        scenes = [
            {
                "scene_id": "01",
                "purpose": "Hook_Problem",
                "duration": 5.0,
                "visual_elements": {
                    "characters": ["athlete in black training gear"],
                    "key_items": ["transparent glass water bottle"],
                    "core_action": "athlete performs a spinning kick that slams the cap off",
                    "visual_setting": "neon-lit gym at night"
                }
            }
        ]
        plan = engine.generate_sfx_plan(scenes)
        self.assertEqual(len(plan.scenes), 1)
        sfx_types = {c.sfx_type for c in plan.scenes[0].sfx_cues}
        self.assertIn("whoosh", sfx_types)
        self.assertIn("impact", sfx_types)

    def test_procedural_sfx_synthesis(self):
        synth = ProceduralSFXSynthesizer()
        whoosh_wav = synth.get_or_synthesize("whoosh", duration=0.4)
        self.assertTrue(whoosh_wav.exists())
        self.assertGreater(whoosh_wav.stat().st_size, 512)

        boom_wav = synth.get_or_synthesize("cinematic_boom", duration=0.8)
        self.assertTrue(boom_wav.exists())
        self.assertGreater(boom_wav.stat().st_size, 512)

    def test_run_tracker_metrics(self):
        tracker = RunTracker(starting_credits=1050)
        tracker.start_stage("test_stage")
        tracker.record_scene_generation(
            scene_id="01",
            compositor_tag="vfx_effectcraft",
            duration=4.5,
            model_tier="quality",
            retries=0,
            success=True
        )
        tracker.end_stage()
        summary = tracker.export_summary()
        self.assertEqual(summary["google_flow_credits"]["initial_credits"], 1050)
        self.assertEqual(summary["google_flow_credits"]["credits_used"], 10)
        self.assertEqual(summary["google_flow_credits"]["credits_remaining"], 1040)
        self.assertIn("test_stage", summary["stage_timings"])

    def test_swappable_llm_provider(self):
        omni = OmniProvider()
        with self.assertRaises(NotImplementedError):
            omni.generate_json("system", "user")

    def test_pipeline_mock_execution(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            brief = {
                "product": "LinearFlow",
                "description": "High-velocity issue tracker",
                "target_audience": "developers"
            }
            llm = GeminiProvider(api_key=None)  # Tests mock fallback without keys
            video = GoogleFlowAutomation(mock_mode=True)
            out_ad = Path(tmp_dir) / "test_final_ad.mp4"

            res = run_pipeline(brief=brief, llm=llm, video=video, output_ad_path=out_ad)
            self.assertTrue(res.exists())
            self.assertGreater(res.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
