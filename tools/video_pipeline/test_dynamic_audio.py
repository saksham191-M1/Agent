"""
test_dynamic_audio.py
─────────────────────
Unit tests for Phase 7:
1. Tone-driven motion profiles (camera never stops rule, push scale ranges).
2. Voices registry (styles, stability, speed).
3. Dynamic audio cue computation from flexible storyboards (3-scene and 7-scene).
"""

import os
import sys
import json
import unittest
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from audio_layer import resolve_voice, load_voices, build_dynamic_cues


class TestDynamicAudioAndMotion(unittest.TestCase):

    def test_motion_profiles_compliance(self):
        """Verifies motion-profiles.json contains required profiles and satisfies camera rules."""
        profile_path = Path(root_dir) / "jarvis" / "remotion" / "engine" / "motion-profiles.json"
        if not profile_path.exists():
            profile_path = Path(root_dir) / "remotion" / "engine" / "motion-profiles.json"

        self.assertTrue(profile_path.exists(), f"motion-profiles.json must exist at {profile_path}")

        with open(profile_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        required_profiles = ["snappy", "smooth", "dramatic"]
        for p_id in required_profiles:
            self.assertIn(p_id, profiles, f"Profile '{p_id}' must be defined in motion-profiles.json")
            prof = profiles[p_id]
            push = prof["camera_push_scale"]
            self.assertEqual(len(push), 2, "push_scale must be [from, to]")
            self.assertGreater(push[1], push[0], "Camera push must always increase (camera never fully stops rule)")
            self.assertIn("easing", prof)
            self.assertIn("text_entry", prof)

    def test_voice_registry_resolution(self):
        """Verifies voices.json maps tone/style to valid ElevenLabs voice configs."""
        voices = load_voices()
        self.assertIn("fast_confident", voices)
        self.assertIn("confident_engineer", voices)
        self.assertIn("calm_precise", voices)

        resolved = resolve_voice("confident_engineer")
        self.assertIn("voice_id", resolved)
        self.assertGreater(resolved.get("speed", 0), 0.5)

    def test_dynamic_cues_3_scene_spec(self):
        """Dynamic audio cues should accurately compute windows for 3-scene storyboard."""
        spec3 = {
            "scenes": [
                {"scene_id": 1, "duration_seconds": 4.0, "voiceover": "Simplicity redefined for work."},
                {"scene_id": 2, "duration_seconds": 4.5, "voiceover": "Everything you need, nothing you do not."},
                {"scene_id": 3, "duration_seconds": 3.5, "voiceover": "Experience it today at acme.com."}
            ]
        }

        cues = build_dynamic_cues(spec3)
        self.assertEqual(cues["total_duration"], 12.0)
        self.assertEqual(len(cues["vo"]), 3)
        # Check start and end window
        self.assertEqual(cues["vo"][0][1], 0.15)  # Scene 1 start offset
        self.assertGreater(len(cues["sfx"]), 3)

    def test_dynamic_cues_7_scene_spec(self):
        """Dynamic audio cues should accurately scale across 7 scenes with 28s total."""
        spec7 = {
            "scenes": [
                {"scene_id": i + 1, "duration_seconds": 4.0, "voiceover": f"Scene {i+1} voice line"}
                for i in range(7)
            ]
        }

        cues = build_dynamic_cues(spec7)
        self.assertEqual(cues["total_duration"], 28.0)
        self.assertEqual(len(cues["vo"]), 7)
        # Verify non-overlapping windows
        for idx in range(len(cues["vo"]) - 1):
            curr_end = cues["vo"][idx][2]
            next_start = cues["vo"][idx + 1][1]
            self.assertLess(curr_end, next_start, f"Scene {idx+1} must end before Scene {idx+2} starts")


if __name__ == "__main__":
    unittest.main()
