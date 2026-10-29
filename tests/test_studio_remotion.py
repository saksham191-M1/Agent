"""Offline bridge checks and opt-in real Remotion exports (no paid API calls)."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.models import StudioError
from studio.remotion_backend import REMOTION_RENDERER_VERSION, _manifest, remotion_status
from studio.render import RenderCancelled
from studio.service import StudioService

BRIEF = {
    "name": "Forma", "description": "A shared workspace.", "audience": "Small teams",
    "benefits": "Keep work together\nReview the next move", "cta": "Explore Forma", "duration": 15,
}


class RemotionBridgeTests(unittest.TestCase):
    def test_manifest_preserves_project_timeline_and_local_assets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logo = root / "logo.png"
            from PIL import Image
            Image.new("RGBA", (24, 24), "#a78bfa").save(logo)
            service = StudioService(root / "projects", load_environment=False)
            project = service.create_project({
                "name": "Forma", "description": "A shared workspace.", "audience": "Small teams",
                "benefits": "Keep work together\nReview the next move", "cta": "Explore Forma",
                "duration": 15, "aspect": "16:9",
            }, logo_path=str(logo))
            render_dir = root / "render"
            render_dir.mkdir()
            manifest_path = _manifest(project, render_dir, "draft", None)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], "16:9")
            self.assertEqual(manifest["quality"], "draft")
            self.assertEqual(manifest["fps"], 24)
            self.assertEqual(manifest["durationSec"], 15)
            self.assertEqual([scene["start"] for scene in manifest["scenes"]], [0, 3, 7, 12])
            self.assertTrue(Path(manifest["assets"]["logo"]).is_file())

    def test_auto_mode_routes_render_through_remotion_when_available(self):
        with tempfile.TemporaryDirectory() as td:
            service = StudioService(Path(td), load_environment=False)
            service.renderer_mode = "auto"
            project = service.create_project({
                "name": "Forma", "description": "A shared workspace.", "audience": "Small teams",
                "benefits": "Keep work together", "cta": "Explore Forma", "duration": 15,
            })
            result = {"video": str(Path(td) / "video.mp4"), "poster": str(Path(td) / "poster.jpg"),
                      "metadata": {"width": 1080, "height": 1920, "fps": 30, "duration": 15, "audio": False},
                      "renderer_version": REMOTION_RENDERER_VERSION}
            with patch("studio.service.remotion_available", return_value=True), patch(
                "studio.service.render_remotion", return_value=result
            ) as renderer:
                rendered = service.render_project(project["id"], quality="final")
            renderer.assert_called_once()
            self.assertEqual(rendered["renders"][-1]["renderer_version"], REMOTION_RENDERER_VERSION)

    def test_runtime_failure_preserves_the_native_dependency_diagnosis(self):
        failure = {"ready": False, "platform": "linux", "stage": "native",
                   "reason": "Run npm ci on linux; Windows and Linux/WSL need separate installations.",
                   "detail": "esbuild was installed for Windows."}
        result = subprocess.CompletedProcess([], 1, json.dumps(failure), "")
        with patch.dict("studio.remotion_backend._runtime_cache", {}, clear=True), \
                patch("studio.remotion_backend.shutil.which", return_value="node"), \
                patch("studio.remotion_backend._runtime_env", return_value={}), \
                patch("studio.remotion_backend.subprocess.run", return_value=result):
            self.assertEqual(remotion_status(), failure)

    def test_runtime_rejects_malformed_or_unsuccessful_ready_status(self):
        for output, returncode in (("[]", 0), ('{"ready": "yes"}', 0), ('{"ready": true}', 1), ("not JSON", 1)):
            result = subprocess.CompletedProcess([], returncode, output, "")
            with self.subTest(output=output), patch.dict("studio.remotion_backend._runtime_cache", {}, clear=True), \
                    patch("studio.remotion_backend.shutil.which", return_value="node"), \
                    patch("studio.remotion_backend._runtime_env", return_value={}), \
                    patch("studio.remotion_backend.subprocess.run", return_value=result):
                self.assertFalse(remotion_status()["ready"])

    def test_required_remotion_failure_is_actionable_and_does_not_publish(self):
        with tempfile.TemporaryDirectory() as td:
            service = StudioService(Path(td), load_environment=False)
            service.renderer_mode = "remotion"
            project = service.create_project(BRIEF)
            reason = "Install FFmpeg/ffprobe or configure FFMPEG_PATH and FFPROBE_PATH for this OS."
            with patch("studio.service.remotion_available", return_value=False), \
                    patch("studio.service.remotion_status", return_value={"ready": False, "reason": reason}), \
                    patch("studio.service.render_video") as fallback:
                with self.assertRaisesRegex(StudioError, "Install FFmpeg/ffprobe"):
                    service.render_project(project["id"], quality="final")
                fallback.assert_not_called()
            saved = service.load_project(project["id"])
            self.assertEqual(saved["status"], "failed")
            self.assertEqual(saved["error"], reason)
            self.assertIsNone(saved["final_path"])
            self.assertEqual(saved["renders"], [])


@unittest.skipUnless(os.environ.get("STUDIO_REMOTION_TESTS") == "1",
                     "Set STUDIO_REMOTION_TESTS=1 for real Remotion bridge exports")
class RealRemotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runtime = remotion_status()
        if not runtime.get("ready"):
            raise RuntimeError(f"Remotion runtime is unavailable: {runtime}")

    def render_project(self, service, project_id, **options):
        try:
            return service.render_project(project_id, **options)
        except RenderCancelled:
            raise
        except StudioError as exc:
            logs = []
            for log in (service.root / project_id / "renders").glob("*/encoder.log"):
                logs.append(log.read_text(encoding="utf-8", errors="replace")[-6000:])
            self.fail(f"{exc}\n" + "\n".join(logs))

    def assert_verified(self, project, quality, width, height, fps, audio):
        self.assertEqual(project["status"], "ready")
        result = project["renders"][-1]
        self.assertTrue(result["renderer_version"].startswith(REMOTION_RENDERER_VERSION + ":"))
        self.assertEqual(result["metadata"]["width"], width)
        self.assertEqual(result["metadata"]["height"], height)
        self.assertEqual(result["metadata"]["fps"], fps)
        self.assertEqual(result["metadata"]["audio"], audio)
        self.assertAlmostEqual(result["metadata"]["duration"], 15, delta=.12)
        self.assertEqual(project[f"{quality}_path"], result["video"])
        self.assertGreater(Path(result["poster"]).stat().st_size, 1000)
        qa = json.loads(Path(result["qa_report"]).read_text(encoding="utf-8"))
        self.assertTrue(qa["passed"])
        self.assertTrue(all(qa["gates"].values()), qa)
        self.assertTrue(qa["gates"]["decode"])
        artifacts = os.environ.get("STUDIO_REMOTION_ARTIFACT_DIR")
        if artifacts:
            destination = Path(artifacts) / f"{quality}-{width}x{height}"
            destination.mkdir(parents=True, exist_ok=True)
            for key in ("video", "poster", "qa_report", "script", "captions", "audio"):
                if result.get(key):
                    source = Path(result[key])
                    shutil.copy2(source, destination / source.name)
        return result, qa

    def test_auto_backend_renders_uploaded_images_and_reuses_a_verified_draft(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logo = root / "logo.png"
            Image.new("RGB", (80, 80), "purple").save(logo)
            images = []
            for index, color in enumerate(("red", "green", "blue", "gold"), 1):
                source = root / f"scene-{index}.png"
                Image.new("RGB", (480, 320), color).save(source)
                images.append(str(source))
            service = StudioService(root / "projects", load_environment=False)
            service.renderer_mode = "auto"
            project = service.create_project({**BRIEF, "aspect": "16:9"}, logo_path=str(logo), scene_image_paths=images)
            with patch("studio.providers.requests.post", side_effect=AssertionError("Unexpected paid provider call")):
                rendered = self.render_project(service, project["id"], quality="draft")
                result, qa = self.assert_verified(rendered, "draft", 640, 360, 24, False)
                self.assertEqual(result["visual_source"], "product_images")
                self.assertEqual(set(qa["assetHashes"]), {"logo", "scene_1", "scene_2", "scene_3", "scene_4"})
                with patch("studio.service.render_remotion", side_effect=AssertionError("Export should be reused")):
                    reused = service.complete_daily_ad(project["id"], quality="draft")
                self.assertEqual(reused["draft_path"], rendered["draft_path"])
                self.assertEqual(len(reused["renders"]), 1)

    def test_final_footage_narration_and_sfx_have_verified_picture_and_sound(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, voice = root / "source.mp4", root / "voice.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "testsrc2=size=320x180:rate=30:duration=3", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(source)], check=True)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=220:duration=0.8", str(voice)], check=True)
            service = StudioService(root / "projects", load_environment=False)
            service.renderer_mode = "remotion"
            project = service.create_project({**BRIEF, "aspect": "1:1"}, demo_path=str(source))
            with patch("studio.providers.requests.post", side_effect=AssertionError("Unexpected paid provider call")), \
                    patch("studio.render.synthesize", return_value=voice) as speech, \
                    patch("studio.render.find_music", return_value=None):
                rendered = self.render_project(service, project["id"], quality="final", narration=True, include_sfx=True)
            result, qa = self.assert_verified(rendered, "final", 1080, 1080, 30, True)
            self.assertEqual(speech.call_count, 4)
            self.assertEqual(result["visual_source"], "screen_recording")
            self.assertTrue(result["sfx"])
            self.assertGreater(qa["peakDb"], -60)
            self.assertLessEqual(qa["peakDb"], .1)
            self.assertTrue(Path(result["sound_cues"]).is_file())
            self.assertIn(project["scenes"][0]["narration"], Path(result["captions"]).read_text(encoding="utf-8"))
            # Compare decoded pixels from the media region, so overlay animation
            # cannot make frozen footage look like successful playback.
            def media_frame(seconds):
                return subprocess.run(["ffmpeg", "-v", "error", "-ss", str(seconds), "-i", result["video"],
                                       "-frames:v", "1", "-vf", "crop=800:300:140:500", "-f", "rawvideo",
                                       "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            first, second = media_frame(.8), media_frame(1.8)
            self.assertTrue(first)
            self.assertNotEqual(first, second, "The supplied footage must actually play")

    def test_cancelled_remotion_is_not_published_and_a_portrait_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            service = StudioService(Path(td) / "projects", load_environment=False)
            service.renderer_mode = "remotion"
            project = service.create_project({**BRIEF, "aspect": "9:16"})
            def cancel_after_start(amount, _message):
                if amount >= .18:
                    self.assertTrue(service.cancel(project["id"]))
            with self.assertRaises(RenderCancelled):
                self.render_project(service, project["id"], progress=cancel_after_start)
            cancelled = service.load_project(project["id"])
            self.assertEqual(cancelled["status"], "cancelled")
            self.assertIsNone(cancelled["draft_path"])
            self.assertEqual(cancelled["renders"], [])
            retried = self.render_project(service, project["id"])
            self.assert_verified(retried, "draft", 360, 640, 24, False)


if __name__ == "__main__":
    unittest.main()
