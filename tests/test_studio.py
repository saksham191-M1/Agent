"""Offline behavior tests; no real API calls, credentials, or repository output writes.
Run: python -m unittest discover -s tests -v
Optional real browser/encoder tests: set STUDIO_RENDER_TESTS=1 first.
"""
import copy
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from studio.models import StudioError, project_rows, template_storyboard, timeline, validate_brief, validate_scenes
from studio.editing import RENDERER_VERSION
from studio.providers import _post, generate_storyboard, generate_strategy, narration_settings, synthesize
from studio.quality import evaluate_script
from studio.render import RenderCancelled, build_audio, build_document, check_export, probe_media, render_video
from studio.service import StudioService
from studio.sound_design import sfx_cues


BRIEF = {
    "name": "Forma", "description": "A shared workspace for planning a team's next product launch.",
    "audience": "Small product teams", "benefits": "Keep launch tasks together\nReview creative in one place\nShare a clear plan",
    "cta": "Explore Forma", "url": "forma.example", "color": "#a78bfa", "template": "spotlight",
    "aspect": "9:16", "duration": 15, "tone": "Confident", "language": "English",
}


class BriefTests(unittest.TestCase):
    def test_valid_brief_and_shared_timeline(self):
        brief = validate_brief(BRIEF)
        scenes = template_storyboard(brief)
        spans = timeline(scenes)
        self.assertEqual([s["duration"] for s in scenes], [3, 4, 5, 3])
        self.assertEqual(spans[-1]["end"], 15)
        for first, second in zip(spans, spans[1:]):
            self.assertEqual(first["end"], second["start"])
        self.assertEqual(scenes[-1]["headline"], BRIEF["cta"])
        self.assertEqual(scenes[-1]["body"], BRIEF["url"])

    def test_problem_solution_uses_supplied_problem_not_invented_claims(self):
        with self.assertRaisesRegex(StudioError, "customer problem"):
            validate_brief({**BRIEF, "template": "problem_solution"})
        problem = "Launch notes live in too many places"
        brief = validate_brief({**BRIEF, "template": "problem_solution", "problem": problem})
        scenes = template_storyboard(brief)
        self.assertEqual(scenes[0]['headline'], problem)
        self.assertEqual(scenes[1]['headline'], 'Meet Forma')
        self.assertNotEqual(scenes[0]['headline'], template_storyboard(validate_brief(BRIEF))[0]['headline'])

    def test_all_durations_and_aspects(self):
        for duration in (15, 20, 30):
            for aspect in ("9:16", "16:9", "1:1"):
                with self.subTest(duration=duration, aspect=aspect):
                    brief = validate_brief({**BRIEF, "duration": duration, "aspect": aspect})
                    self.assertAlmostEqual(sum(s["duration"] for s in template_storyboard(brief)), duration)

    def test_rejects_missing_brief_and_invalid_options(self):
        for key, value in [("name", ""), ("description", ""), ("benefits", ""), ("audience", ""),
                           ("color", "purple"), ("duration", 14), ("duration", float("nan")),
                           ("aspect", "4:3"), ("url", "file:///local"), ("name", "a" * 41)]:
            with self.subTest(key=key, value=value), self.assertRaises(StudioError):
                validate_brief({**BRIEF, key: value})

    def test_durations_and_scene_types_are_not_silently_coerced(self):
        scenes = template_storyboard(validate_brief(BRIEF))
        for value in ("not a duration", float("nan"), float("inf"), -1, 50, True):
            bad = copy.deepcopy(scenes)
            bad[0]["duration"] = value
            with self.subTest(value=value), self.assertRaises(StudioError):
                validate_scenes(bad, 15)
        bad = copy.deepcopy(scenes)
        bad[0]["duration"] = 4
        with self.assertRaisesRegex(StudioError, "add up"):
            validate_scenes(bad, 15)
        with self.assertRaises(StudioError):
            validate_scenes(scenes[:-1], 15)

    def test_sound_design_cues_follow_the_shared_scene_timeline(self):
        scenes = template_storyboard(validate_brief(BRIEF))
        cues = sfx_cues(scenes)
        names = [name for name, _ in cues]
        self.assertEqual(names.count("whoosh"), 4)
        self.assertEqual(names.count("swipe"), 4)
        self.assertEqual(names.count("pop"), 2)
        self.assertEqual(names.count("ding"), 1)
        self.assertNotIn("click", names)
        self.assertEqual(cues[0], ("whoosh", 0.0))
        self.assertTrue(all(0 <= start <= 15 for _, start in cues))

    def test_sound_design_accepts_non_ad_scene_names(self):
        scenes = [{"kind": "Dialogue", "duration": 2}, {"kind": "Action", "duration": 3},
                  {"kind": "Ending", "duration": 2}]
        cues = sfx_cues(scenes)
        names = [name for name, _ in cues]
        self.assertEqual(names.count("whoosh"), 3)
        self.assertEqual(names.count("swipe"), 2)
        self.assertEqual(names.count("pop"), 1)
        self.assertEqual(names.count("ding"), 1)


class ProviderTests(unittest.TestCase):
    def test_missing_ai_configuration_never_falls_back(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GEMINI_MODEL": ""}), patch("studio.providers.requests.post") as post:
            with self.assertRaisesRegex(StudioError, "GEMINI_MODEL"):
                generate_storyboard(validate_brief(BRIEF))
            post.assert_not_called()

    def test_provider_retries_are_bounded_and_error_is_safe(self):
        response = Mock(status_code=503)
        with patch("studio.providers.requests.post", return_value=response) as post, patch("studio.providers.time.sleep"):
            with self.assertRaisesRegex(StudioError, "rate-limited"):
                _post("https://provider.invalid", headers={}, payload={}, provider="Test")
            self.assertEqual(post.call_count, 3)
            self.assertEqual(post.call_args.kwargs["timeout"], (10, 90))

    def test_auth_error_does_not_retry_or_return_demo_copy(self):
        with patch("studio.providers.requests.post", return_value=Mock(status_code=401)) as post:
            with self.assertRaisesRegex(StudioError, "credentials"):
                _post("https://provider.invalid", headers={}, payload={}, provider="Test")
            self.assertEqual(post.call_count, 1)

    def test_strategy_then_script_result_and_invalid_strategy(self):
        brief = validate_brief(BRIEF)
        strategy = {"concept_name": "One clear launch", "core_promise": "Keep launch work together",
                    "audience_insight": "Small teams lose momentum when feedback is scattered.",
                    "hook_type": "curiosity", "hook_options": ["What if launch work lived in one place?", "Still searching for the latest launch version?", "Scattered feedback slows launches."],
                    "selected_hook": "What if launch work lived in one place?", "emotional_arc": ["friction", "recognition", "relief", "action"],
                    "lead_benefit": "Keep launch tasks together", "proof_method": "benefit_card",
                    "visual_strategy": "Show scattered notes becoming one clear workspace.", "cta_strategy": "Connect the CTA to clarity.",
                    "risk_notes": ["Do not invent metrics."]}
        scenes = [
            {"kind": "Hook", "headline": strategy["selected_hook"], "body": "Launch work gets scattered.", "narration": "Launch notes scattered again?", "duration": 3},
            {"kind": "Benefit", "headline": "Keep launch work together", "body": "Tasks and decisions stay connected.", "narration": "Bring your launch tasks into Forma.", "duration": 4},
            {"kind": "Product", "headline": "See the next move", "body": "Review creative in one place.", "narration": "Review creative together and share a clear launch plan.", "duration": 5},
            {"kind": "Call to action", "headline": "Explore Forma", "body": "forma.example", "narration": "Plan together. Explore Forma.", "duration": 3},
        ]
        strategy_response = Mock(status_code=200)
        strategy_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": json.dumps(strategy)}]}}]}
        script_response = Mock(status_code=200)
        script_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": json.dumps({"scenes": scenes})}]}}]}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-only", "GEMINI_MODEL": "configured-model"}), patch("studio.providers._post", side_effect=[strategy_response, script_response]) as post:
            generated, saved_strategy = generate_storyboard(brief, return_strategy=True)
            self.assertEqual(generated, scenes)
            self.assertEqual(saved_strategy["model"], "configured-model")
            self.assertEqual(post.call_count, 2)
        # A long line or changed timeline gets one repair; broken output cannot trigger unbounded calls.
        long_lines = copy.deepcopy(scenes)
        long_lines[0]["narration"] = "Your launch notes keep getting scattered across too many different places."
        wrong_timing = copy.deepcopy(scenes)
        wrong_timing[0]["duration"], wrong_timing[1]["duration"] = 4, 3
        for bad in (long_lines, wrong_timing):
            with self.subTest(bad=bad[0]), patch.dict(os.environ, {"GEMINI_API_KEY": "test-only", "GEMINI_MODEL": "configured-model"}), \
                    patch("studio.providers._generate_json", side_effect=[strategy, {"scenes": bad}, {"scenes": scenes}]) as generate:
                self.assertEqual(generate_storyboard(brief), scenes)
                self.assertEqual(generate.call_count, 3)
                self.assertIn("QUALITY FEEDBACK", generate.call_args.args[0])
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-only", "GEMINI_MODEL": "configured-model"}), \
                patch("studio.providers._generate_json", side_effect=[strategy, {"scenes": long_lines}, {"scenes": long_lines}]) as generate:
            with self.assertRaisesRegex(StudioError, "one bounded repair"):
                generate_storyboard(brief)
            self.assertEqual(generate.call_count, 3)
        invalid = Mock(status_code=200)
        invalid.json.return_value = {"candidates": []}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-only", "GEMINI_MODEL": "configured-model"}), patch("studio.providers._post", return_value=invalid):
            with self.assertRaisesRegex(StudioError, "creative strategy"):
                generate_strategy(brief)

    def test_quality_gate_rejects_generic_headline_only_copy(self):
        brief = validate_brief(BRIEF)
        strategy = {"selected_hook": "What if launch work lived in one place?"}
        scenes = template_storyboard(brief)
        result = evaluate_script(scenes, brief, strategy)
        self.assertFalse(result["passed"])
        self.assertTrue(any("generic product" in error for error in result["errors"]))
        self.assertFalse(any("only repeats" in error for error in result["errors"]))

    def test_speech_is_explicit_and_cached(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}), self.assertRaisesRegex(StudioError, "Narration needs"):
                synthesize("Hello", Path(td))
            response = Mock(content=b"synthetic-test-audio", headers={"Content-Type": "audio/mpeg"})
            with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test-only", "ELEVENLABS_VOICE_ID": "test-voice"}), patch("studio.providers._post", return_value=response) as post:
                first = synthesize("Hello", Path(td))
                self.assertEqual(first, synthesize("Hello", Path(td)))
                self.assertEqual(post.call_count, 1)

    def test_premade_voice_default_and_payment_error(self):
        with patch.dict(os.environ, {"ELEVENLABS_VOICE_ID": ""}):
            self.assertEqual(narration_settings()["voice"], "EXAVITQu4vr4xnSDxMaL")
        with patch("studio.providers.requests.post", return_value=Mock(status_code=402)) as post:
            with self.assertRaisesRegex(StudioError, "premade voice"):
                _post("https://provider.invalid", headers={}, payload={}, provider="ElevenLabs")
            self.assertEqual(post.call_count, 1)

    def test_overlong_narration_stops_before_speech_requests(self):
        project = {"brief": validate_brief(BRIEF), "scenes": template_storyboard(validate_brief(BRIEF))}
        project["scenes"][-1]["narration"] = "This last line is too long to fit in three seconds."
        with patch("studio.render.synthesize") as speech:
            with self.assertRaisesRegex(StudioError, "Call to action"):
                build_audio(project, Path("unused"), Path("unused"), lambda *_: None, threading.Event())
            speech.assert_not_called()


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.service = StudioService(self.root, load_environment=False)
        self.project = self.service.create_project(BRIEF)

    def tearDown(self):
        self.temp.cleanup()

    def test_projects_persist_and_can_be_reopened(self):
        restarted = StudioService(self.root, load_environment=False)
        self.assertEqual(restarted.load_project(self.project["id"])["scenes"], self.project["scenes"])
        self.assertEqual(restarted.list_projects()[0]["name"], BRIEF["name"])
        self.assertTrue(Path(self.project["project_path"]).is_file())

    def test_template_mode_has_no_network_and_is_labeled(self):
        with patch("studio.providers.requests.post") as post:
            p = self.service.create_project(BRIEF)
            post.assert_not_called()
            self.assertTrue(any("not AI-generated" in w for w in p["warnings"]))

    def test_repeated_projects_have_isolated_ids(self):
        second = self.service.create_project(BRIEF)
        self.assertNotEqual(second["id"], self.project["id"])
        self.assertEqual(len(self.service.list_projects()), 2)

    def test_edits_are_saved_and_invalidate_old_outputs(self):
        p = self.project
        p.update(final_path="old.mp4", draft_path="old-draft.mp4", status="ready")
        self.service._save(p)
        rows = project_rows(p)
        rows[0][1] = "One clear place to plan"
        saved = self.service.update_storyboard(p["id"], rows)
        self.assertEqual(saved["revision"], 2)
        self.assertIsNone(saved["final_path"])
        self.assertIsNone(saved["draft_path"])
        self.assertEqual(self.service.load_project(p["id"])["scenes"][0]["headline"], rows[0][1])

    def test_invalid_edit_does_not_change_saved_project(self):
        rows = project_rows(self.project)
        rows[0][-1] = 10
        with self.assertRaises(StudioError):
            self.service.update_storyboard(self.project["id"], rows)
        self.assertEqual(self.service.load_project(self.project["id"])["scenes"], self.project["scenes"])

    def test_save_recovers_from_transient_windows_lock_without_losing_old_data(self):
        original_replace = Path.replace
        blocked = PermissionError("Temporary Windows sharing violation")
        blocked.winerror = 32
        calls = []
        def replace(source, target):
            calls.append(source)
            if len(calls) == 1:
                raise blocked
            return original_replace(source, target)
        rows = project_rows(self.project)
        rows[0][1] = "Keep your launch together"
        with patch.object(Path, "replace", new=replace), patch("studio.locking.time.sleep"):
            saved = self.service.update_storyboard(self.project["id"], rows)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.service.load_project(saved["id"])["scenes"][0]["headline"], rows[0][1])
        before = Path(saved["project_path"]).read_bytes()
        rows[0][1] = "This edit cannot be published yet"
        with patch.object(Path, "replace", side_effect=blocked) as replace, patch("studio.locking.time.sleep"):
            with self.assertRaises(PermissionError):
                self.service.update_storyboard(saved["id"], rows)
            self.assertEqual(replace.call_count, 5)
        self.assertEqual(Path(saved["project_path"]).read_bytes(), before)

    def test_success_requires_a_successful_renderer_result(self):
        result = {"video": str(self.root / "test.mp4"), "poster": str(self.root / "poster.jpg"), "metadata": {"duration": 15}}
        with patch("studio.service.render_video", return_value=result):
            p = self.service.render_project(self.project["id"], "final")
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["final_path"], result["video"])
        self.assertEqual(p["renders"][0]["revision"], 1)
        with patch("studio.service.render_video", side_effect=StudioError("Encoder unavailable")):
            with self.assertRaisesRegex(StudioError, "Encoder unavailable"):
                self.service.render_project(p["id"], "final")
        failed = self.service.load_project(p["id"])
        self.assertEqual(failed["status"], "failed")
        self.assertIsNone(failed["final_path"])

    def test_cancel_and_retry_state(self):
        def cancelled(project, directory, quality, narrated, cache, progress, event, *, include_sfx=False):
            self.assertTrue(self.service.cancel(project["id"]))
            self.assertTrue(event.is_set())
            raise RenderCancelled("Cancelled by user")
        with patch("studio.service.render_video", side_effect=cancelled), self.assertRaises(RenderCancelled):
            self.service.render_project(self.project["id"])
        self.assertEqual(self.service.load_project(self.project["id"])["status"], "cancelled")
        self.assertFalse(self.service.cancel(self.project["id"]))
        self.assertFalse(self.service._render_lock.locked())

    def test_invalid_project_and_render_busy(self):
        with self.assertRaises(StudioError):
            self.service.load_project("not-a-project-id")
        self.service._render_lock.acquire()
        try:
            with self.assertRaisesRegex(StudioError, "Another video"):
                self.service.render_project(self.project["id"])
        finally:
            self.service._render_lock.release()

    def test_sfx_is_forwarded_without_narration_and_persisted(self):
        result = {"video": str(self.root / "sfx.mp4"), "poster": str(self.root / "poster.jpg"),
                  "metadata": {"duration": 15, "audio": True}, "renderer_version": RENDERER_VERSION}
        with patch("studio.service.render_video", return_value=result) as render:
            saved = self.service.render_project(self.project["id"], narration=False, include_sfx=True)
        self.assertFalse(render.call_args.args[3])
        self.assertTrue(render.call_args.kwargs["include_sfx"])
        self.assertTrue(saved["renders"][-1]["sfx"])
        self.assertFalse(saved["renders"][-1]["narrated"])

    def test_interrupted_render_does_not_stay_running(self):
        self.project["status"] = "rendering"
        self.service._save(self.project)
        reopened = StudioService(self.root, load_environment=False)
        self.assertEqual(reopened.load_project(self.project["id"])["status"], "failed")

    def test_image_upload_is_normalized_and_copied(self):
        from PIL import Image
        source = self.root / "source.jpg"
        Image.new("RGB", (400, 300), "purple").save(source)
        p = self.service.create_project(BRIEF, screenshot_path=str(source))
        copied = Path(p["assets"]["screenshot"])
        self.assertNotEqual(source, copied)
        with Image.open(copied) as image:
            self.assertEqual(image.format, "PNG")
        source.write_text("not an image")
        with self.assertRaises(StudioError):
            self.service.create_project(BRIEF, screenshot_path=str(source))
        self.assertEqual(len(self.service.list_projects()), 2)

    def test_composition_uses_data_not_interpolated_markup(self):
        self.project["scenes"][0]["headline"] = 'Design <better> & "clearer"'
        document = build_document(self.project, False)
        self.assertNotIn('__PROJECT_JSON__', document)
        self.assertIn('\\u003cbetter\\u003e', document)
        self.assertNotIn('fonts.googleapis.com', document)


class ExportChecks(unittest.TestCase):
    def test_rejects_missing_audio_or_short_video(self):
        info = {"format": {"duration": "15"}, "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920, "r_frame_rate": "30/1"}]}
        with patch("studio.render.probe_media", return_value=info):
            self.assertFalse(check_export(Path("fake.mp4"), 1080, 1920, 30, 15, False)["audio"])
            with self.assertRaisesRegex(StudioError, "audio"):
                check_export(Path("fake.mp4"), 1080, 1920, 30, 15, True)
            info["format"]["duration"] = "12.57"
            with self.assertRaisesRegex(StudioError, "duration"):
                check_export(Path("fake.mp4"), 1080, 1920, 30, 15, False)


@unittest.skipUnless(os.environ.get("STUDIO_RENDER_TESTS") == "1", "Set STUDIO_RENDER_TESTS=1 for real local rendering")
class LocalRenderTests(unittest.TestCase):
    def test_real_browser_to_ffmpeg_video(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = StudioService(root / "projects", load_environment=False)
            project = service.create_project(BRIEF)
            result = render_video(project, root / "render", "draft", False, root / "cache", lambda *_: None,
                                  threading.Event(), dimensions=(180, 320), frame_rate=8)
            info = check_export(Path(result["video"]), 180, 320, 8, 15, False)
            self.assertAlmostEqual(info["duration"], 15, places=1)
            self.assertGreater(Path(result["poster"]).stat().st_size, 1000)

    def test_real_narrated_export_has_aac_and_scene_captions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = StudioService(root / "projects", load_environment=False).create_project(BRIEF)
            voice = root / "voice.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=frequency=220:duration=0.8", str(voice)], check=True)
            with patch("studio.render.synthesize", return_value=voice):
                result = render_video(project, root / "render", "draft", True, root / "cache", lambda *_: None,
                                      threading.Event(), dimensions=(180, 320), frame_rate=8)
            self.assertTrue(check_export(Path(result["video"]), 180, 320, 8, 15, True)["audio"])
            streams = probe_media(Path(result["video"]))["streams"]
            self.assertTrue(any(s["codec_name"] == "aac" for s in streams))
            self.assertEqual(Path(result["audio"]).name, "narration.wav")
            self.assertIn(project["scenes"][0]["narration"], Path(result["script"]).read_text(encoding="utf-8"))
            captions = Path(result["captions"]).read_text(encoding="utf-8")
            self.assertIn("00:00:00,200 --> 00:00:02,800", captions)
            self.assertIn("00:00:12,200 --> 00:00:14,800", captions)

    def test_real_audio_mix_uses_scene_boundaries_without_paid_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = StudioService(root / "projects", load_environment=False).create_project(BRIEF)
            tone = root / "tone.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=0.8", str(tone)], check=True)
            with patch("studio.render.synthesize", return_value=tone):
                mixed = build_audio(project, root, root / "cache", lambda *_: None, threading.Event())
            self.assertAlmostEqual(float(probe_media(mixed)["format"]["duration"]), 15, places=1)
            # All four short lines should have silence after their window, not bleed into later scenes.
            result = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mixed), "-f", "f32le", "-ac", "1", "-ar", "1000", "-"], capture_output=True, check=True)
            import array
            samples = array.array("f", result.stdout)
            for scene in timeline(project["scenes"]):
                start = round((scene["start"] + .35) * 1000)
                self.assertGreater(max(abs(x) for x in samples[start:start + 300]), .01)
                silent = round((scene["end"] - .5) * 1000)
                self.assertLess(max(abs(x) for x in samples[silent:silent + 250]), .002)


if __name__ == "__main__":
    unittest.main()
