"""Product evidence, genuine footage, and standalone SFX regression checks."""
import array
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.assets import normalize_video
from studio.editing import shot_plan
from studio.models import StudioError
from studio.render import build_audio, check_export, render_video, serve_video
from studio.service import StudioService

BRIEF = {"name": "Product", "description": "A shared workspace for product projects.",
         "audience": "Small teams", "benefits": ["Keep project work together"], "duration": 15}


class EditorialTests(unittest.TestCase):
    def test_shots_cover_every_frame_and_do_not_leave_long_middle_holds(self):
        scenes = [{"kind": kind, "duration": seconds} for kind, seconds in
                  (("Hook", 3), ("Benefit", 4), ("Product", 5), ("Call to action", 3))]
        shots = shot_plan(scenes)
        self.assertEqual(shots[0]["start"], 0)
        self.assertEqual(shots[-1]["end"], 15)
        self.assertGreater(len(shots), len(scenes))
        for first, second in zip(shots, shots[1:]):
            self.assertEqual(first["end"], second["start"])
        self.assertTrue(all(shot["end"] - shot["start"] <= 2.1 for shot in shots[:-1]))
        self.assertEqual(shots[-1]["framing"], "wide")

    def test_unverified_or_missing_video_does_not_create_a_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = StudioService(root / "projects", load_environment=False)
            with self.assertRaisesRegex(StudioError, "recording"):
                service.create_project(BRIEF, demo_path=str(root / "missing.mp4"))
            self.assertEqual(service.list_projects(), [])


@unittest.skipUnless(os.environ.get("STUDIO_RENDER_TESTS") == "1", "Set STUDIO_RENDER_TESTS=1 for footage/audio checks")
class RealProductMediaTests(unittest.TestCase):
    def test_sfx_only_export_is_audible_and_never_requests_a_voice(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = StudioService(root / "projects", load_environment=False).create_project(BRIEF)
            # Narration can be invalid/empty without preventing an SFX-only mix.
            project["scenes"][0]["narration"] = ""
            with patch("studio.render.synthesize") as speech, patch("studio.render.find_music", return_value=None):
                result = render_video(project, root / "render", "draft", False, root / "cache", lambda *_: None,
                                      threading.Event(), dimensions=(180, 320), frame_rate=8, include_sfx=True)
                speech.assert_not_called()
            self.assertTrue(check_export(Path(result["video"]), 180, 320, 8, 15, True)["audio"])
            self.assertTrue(result["sfx"])
            self.assertIsNone(result["narration_settings"])
            self.assertEqual(Path(result["audio"]).name, "sound_design.wav")
            decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", result["video"], "-f", "f32le",
                                      "-ac", "1", "-ar", "48000", "-"], capture_output=True, check=True)
            samples = array.array("f", decoded.stdout)
            # Intro, intra-scene cut, and end card all contain actual sound.
            for start in (.05, 1.5, 12.55):
                window = samples[round(start * 48000):round((start + .15) * 48000)]
                self.assertGreater(max(map(abs, window)), .04)
            self.assertLess(max(map(abs, samples)), 1)

    def test_footage_is_copied_muted_and_seekable_at_original_speed(self):
        from playwright.sync_api import sync_playwright
        from studio.render import build_document
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15:duration=3",
                            "-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", str(source)], check=True)
            service = StudioService(root / "projects", load_environment=False)
            product = service.save_product(None, BRIEF, demo_path=str(source))
            project = service.create_daily_project(product["id"])
            copied = Path(project["assets"]["demo"])
            self.assertNotEqual(copied, Path(product["assets"]["demo"]))
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                try:
                    page = browser.new_page(viewport={"width": 360, "height": 640})
                    page.route("**/*", lambda route: serve_video(route, copied)
                               if route.request.url == "https://studio.local/demo.mp4" else route.abort())
                    page.set_content(build_document(project, False).replace('<head>', '<head><base href="https://studio.local/">'))
                    self.assertTrue(page.evaluate("window.ready"))
                    page.evaluate("window.renderAt", .5)
                    first = page.screenshot()
                    pixels = page.evaluate("""() => {const v=document.querySelector('video'), c=document.createElement('canvas');
                        c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL();}""")
                    self.assertAlmostEqual(page.locator('video').evaluate('v=>v.currentTime'), .5, places=2)
                    page.evaluate("window.renderAt", 1.5)
                    self.assertNotEqual(first, page.screenshot())
                    later_pixels = page.evaluate("""() => {const v=document.querySelector('video'), c=document.createElement('canvas');
                        c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL();}""")
                    self.assertNotEqual(pixels, later_pixels, "The actual footage pixels must change, not just the overlay text")
                    page.evaluate("window.renderAt", .5)
                    self.assertAlmostEqual(page.locator('video').evaluate('v=>v.currentTime'), .5, places=2)
                    self.assertTrue(page.locator('video').evaluate('v=>v.muted'))
                    self.assertFalse(page.locator('#board').is_visible())
                finally:
                    browser.close()
            result = render_video(project, root / "render", "draft", False, root / "cache", lambda *_: None,
                                  threading.Event(), dimensions=(180, 320), frame_rate=8, include_sfx=True)
            self.assertEqual(result["visual_source"], "screen_recording")
            self.assertTrue(check_export(Path(result["video"]), 180, 320, 8, 15, True)["audio"])
            self.assertTrue((root / "render" / "demo.mp4").is_file())
            # Source replacement cannot alter the project's copied reference.
            before = copied.read_bytes()
            source.write_bytes(b"replaced upload")
            self.assertEqual(copied.read_bytes(), before)
