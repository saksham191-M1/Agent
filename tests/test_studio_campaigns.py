"""Offline product import, review, persistence, and daily automation contracts."""
import copy
import json
import os
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from studio.catalog import ProductCatalog, source_key
from studio.editing import RENDERER_VERSION
from studio.creative import duplicate_reason, rotated_brief, select_plan, signature, variant_storyboard
from studio.locking import FileLock
from studio.models import StudioError, project_rows
from studio.providers import narration_settings
from studio.service import StudioService

BRIEF = dict(name="Forma", description="Plan a product launch in a shared workspace.", audience="Small product teams",
             problem="Launch information is scattered across tools.", benefits=["Keep launch tasks together", "Review creative in one place", "Share a clear launch plan"],
             cta="Explore Forma", url="https://forma.example", color="#a78bfa", duration=15, aspect="9:16", template="spotlight")


def discovery_fixture(url, destination, progress=None):
    from PIL import Image
    destination.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), "#a78bfa").save(destination / "logo.png")
    return {"url": url, "brief": {k: BRIEF[k] for k in ("name", "description", "benefits", "url", "color")},
            "assets": {"logo": str((destination / "logo.png").resolve())},
            "brand": {"colors": ["#a78bfa"], "fonts": ["Inter"]},
            "sources": [{"url": url, "title": "Forma"}],
            "evidence": [{"field": "name", "value": "Forma", "source": url, "method": "metadata", "confidence": "high"}],
            "warnings": ["Public claims need review."], "missing": ["audience"], "discovered_at": "2026-01-01T00:00:00+00:00"}


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = StudioService(self.root, load_environment=False)

    def product(self):
        return self.service.save_product(None, BRIEF)

    def test_import_is_partial_reviewable_and_cached(self):
        with patch("studio.discovery.discover_site", side_effect=discovery_fixture) as discover:
            first = self.service.import_product("forma.example")
            self.assertFalse(first["approved"])
            self.assertEqual(first["brief"]["audience"], "")
            self.assertTrue(Path(first["assets"]["logo"]).is_file())
            second = self.service.import_product("https://forma.example/?tracking=ignored")
            self.assertEqual(second["id"], first["id"])
            self.assertEqual(discover.call_count, 1)
        with self.assertRaisesRegex(StudioError, "Review"):
            self.service.create_daily_project(first["id"])
        saved = self.service.save_product(first["id"], {**first["brief"], "audience": BRIEF["audience"]})
        self.assertTrue(saved["approved"])
        self.assertEqual(saved["discovery"]["evidence"][0]["source"], "https://forma.example/")

    def test_refresh_preserves_reviewed_facts_and_previous_ad_assets(self):
        with patch("studio.discovery.discover_site", side_effect=discovery_fixture):
            p = self.service.import_product("forma.example")
            saved = self.service.save_product(p["id"], BRIEF)
            old_asset = saved["assets"]["logo"]
            project = self.service.create_daily_project(p["id"], campaign_date="2026-01-01")
            with patch("studio.discovery.discover_site", return_value={**discovery_fixture("https://forma.example/", self.root / "new"),
                                                                       "brief": {"name": "Unreviewed new name"}}):
                refreshed = self.service.import_product("forma.example", refresh=True)
            self.assertEqual(refreshed["brief"]["name"], "Forma")
            self.assertEqual(refreshed["assets"]["logo"], old_asset)
            self.assertEqual(refreshed["pending_discovery"]["brief"]["name"], "Unreviewed new name")
            self.assertEqual(self.service.load_project(project["id"])["name"], "Forma")
            self.assertNotEqual(project["assets"]["logo"], old_asset)
            self.assertTrue(Path(project["assets"]["logo"]).is_file())

    def test_import_failure_does_not_replace_saved_profile(self):
        with patch("studio.discovery.discover_site", side_effect=discovery_fixture):
            p = self.service.import_product("forma.example")
        with patch("studio.discovery.discover_site", side_effect=StudioError("Website unavailable")):
            with self.assertRaises(StudioError):
                self.service.import_product("forma.example", refresh=True)
        self.assertEqual(self.service.load_product(p["id"])["brief"], p["brief"])

    def test_profile_revision_changes_only_when_content_changes(self):
        p = self.product()
        same = self.service.save_product(p["id"], BRIEF)
        self.assertEqual(same["revision"], p["revision"])
        changed = self.service.save_product(p["id"], {**BRIEF, "cta": "See the workspace"})
        self.assertEqual(changed["revision"], 2)
        restarted = StudioService(self.root, load_environment=False)
        self.assertEqual(restarted.load_product(p["id"])["brief"]["cta"], "See the workspace")

    def test_four_scene_images_survive_profile_and_daily_project_copy(self):
        from PIL import Image
        images = []
        for index, color in enumerate(("red", "green", "blue", "gold")):
            image = self.root / f"source-{index}.png"
            Image.new("RGB", (160, 100), color).save(image)
            images.append(str(image))
        product = self.service.save_product(None, BRIEF, scene_image_paths=images)
        ad = self.service.create_daily_project(product["id"])
        original = Path(ad["assets"]["scene_1"]).read_bytes()
        Image.new("RGB", (160, 100), "white").save(images[0])
        changed = self.service.save_product(product["id"], BRIEF, scene_image_paths=images)
        self.assertEqual(changed["revision"], 2)
        self.assertEqual(Path(ad["assets"]["scene_1"]).read_bytes(), original)
        self.assertNotEqual(Path(changed["assets"]["scene_1"]).read_bytes(), original)
        self.assertTrue(all(Path(ad["assets"][f"scene_{i}"]).is_file() for i in range(1, 5)))
        self.assertFalse(any("No screenshot" in warning for warning in ad["warnings"]))
        with self.assertRaisesRegex(StudioError, "four scene images"):
            self.service.create_project(BRIEF, scene_image_paths=images[:3])

    def test_same_date_is_idempotent_even_after_restart(self):
        p = self.product()
        with patch("studio.service.generate_storyboard") as ai:
            first = self.service.create_daily_project(p["id"], campaign_date="2026-01-01")
            restarted = StudioService(self.root, load_environment=False)
            second = restarted.create_daily_project(p["id"], campaign_date="2026-01-01", copy_mode="gemini")
            self.assertEqual(first["id"], second["id"])
            self.assertTrue(second["reused_daily"])
            ai.assert_not_called()
        self.assertEqual(len(restarted.list_product_ads(p["id"])), 1)

    def test_thirty_daily_plans_change_angles_looks_and_lead_benefits(self):
        p = self.product()
        projects = []
        for day in range(30):
            iso_day = (date(2026, 1, 1) + timedelta(days=day)).isoformat()
            ad = self.service.create_daily_project(p["id"], campaign_date=iso_day)
            projects.append(ad)
            self.assertEqual(ad["brief"]["color"], BRIEF["color"])
            self.assertEqual(ad["brief"]["cta"], BRIEF["cta"])
            self.assertEqual(set(ad["brief"]["benefits"]), set(BRIEF["benefits"]))
            self.assertEqual(ad["campaign"]["ordinal"], day + 1)
            self.assertAlmostEqual(sum(s["duration"] for s in ad["scenes"]), 15)
            if day:
                self.assertNotEqual(ad["scenes"][0]["headline"], projects[-2]["scenes"][0]["headline"])
        self.assertEqual(len({p["creative"]["key"] for p in projects}), 30)
        self.assertEqual(len({p["creative"]["signature"] for p in projects}), 30)
        self.assertEqual(len({p["creative"]["angle"] for p in projects}), 6)
        self.assertEqual(len({p["creative"]["look"] for p in projects}), 3)

    def test_explicit_new_take_keeps_previous_project(self):
        p = self.product()
        first = self.service.create_daily_project(p["id"], campaign_date="2026-01-01")
        second = self.service.create_daily_project(p["id"], campaign_date="2026-01-01", new_take=True)
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["campaign"]["take"], 2)
        self.assertEqual(self.service.load_project(first["id"])["scenes"], first["scenes"])
        self.assertEqual(self.service.create_daily_project(p["id"], campaign_date="2026-01-01")["id"], second["id"])

    def test_pool_exhaustion_is_explicit_not_random_duplicate(self):
        p = self.product()
        count = 0
        for attempt in range(80):
            try:
                self.service.create_daily_project(p["id"], campaign_date="2026-01-01", new_take=True)
                count += 1
            except StudioError as exc:
                self.assertIn("exhausted", str(exc))
                break
        else:
            self.fail("A bounded creative pool should not generate infinitely many fake variations")
        self.assertGreaterEqual(count, 30)
        self.assertEqual(len(self.service.list_product_ads(p["id"])), count)

    def test_goal_selects_matching_verified_benefit(self):
        p = self.product()
        ad = self.service.create_daily_project(p["id"], goal="Focus on reviewing creative")
        self.assertEqual(ad["creative"]["lead_benefit"], "Review creative in one place")

    def test_invalid_date_and_unapproved_profile_do_not_create_ads(self):
        p = self.product()
        with self.assertRaisesRegex(StudioError, "YYYY-MM-DD"):
            self.service.create_daily_project(p["id"], campaign_date="tomorrow")
        self.assertEqual(self.service.list_product_ads(p["id"]), [])

    def test_copy_failure_does_not_consume_a_daily_slot(self):
        p = self.product()
        with patch("studio.service.generate_storyboard", side_effect=StudioError("Provider unavailable")):
            with self.assertRaises(StudioError):
                self.service.create_daily_project(p["id"], copy_mode="gemini")
        self.assertEqual(self.service.list_product_ads(p["id"]), [])
        success = self.service.create_daily_project(p["id"])
        self.assertEqual(success["campaign"]["ordinal"], 1)

    def test_repeated_ai_copy_gets_only_one_regeneration_attempt(self):
        p = self.product()
        first = self.service.create_daily_project(p["id"], campaign_date="2026-01-01")
        with patch("studio.service.generate_storyboard", return_value=first["scenes"]) as ai:
            with self.assertRaisesRegex(StudioError, "repeated"):
                self.service.create_daily_project(p["id"], campaign_date="2026-01-02", copy_mode="gemini")
            self.assertEqual(ai.call_count, 2)
        self.assertEqual(len(self.service.list_product_ads(p["id"])), 1)

    def test_render_retry_keeps_same_script_and_verified_export_is_reused(self):
        p = self.product()
        output = self.root / "final.mp4"
        output.write_bytes(b"fixture")
        result = {"video": str(output), "poster": str(self.root / "poster.jpg"), "metadata": {"duration": 15},
                  "renderer_version": RENDERER_VERSION}
        with patch("studio.service.render_video", side_effect=StudioError("Encoder unavailable")):
            with self.assertRaises(StudioError):
                self.service.generate_daily_ad(p["id"], campaign_date="2026-01-01")
        failed = self.service.list_product_ads(p["id"])[0]
        self.assertEqual(failed["status"], "failed")
        with patch("studio.service.render_video", return_value=result) as renderer:
            ready = self.service.generate_daily_ad(p["id"], campaign_date="2026-01-01")
            self.assertEqual(ready["id"], failed["id"])
            renderer.assert_called_once()
        with patch("studio.service.check_export", return_value=result["metadata"]), patch("studio.service.render_video") as renderer:
            cached = self.service.generate_daily_ad(p["id"], campaign_date="2026-01-01")
            self.assertEqual(cached["final_path"], str(output))
            renderer.assert_not_called()
        with patch("studio.service.check_export", side_effect=StudioError("corrupt")), patch("studio.service.render_video", return_value=result) as renderer:
            self.service.generate_daily_ad(p["id"], campaign_date="2026-01-01")
            renderer.assert_called_once()

    def test_local_process_lock_and_restart_do_not_corrupt_running_job(self):
        ad = self.service.create_project(BRIEF)
        ad["status"] = "rendering"
        self.service._save(ad)
        lock = FileLock(self.root / ".render.lock", "busy")
        with lock:
            restarted = StudioService(self.root, load_environment=False)
            self.assertEqual(restarted.load_project(ad["id"])["status"], "rendering")
            with self.assertRaises(StudioError):
                restarted.render_project(ad["id"])
        recovered = StudioService(self.root, load_environment=False)
        self.assertEqual(recovered.load_project(ad["id"])["status"], "failed")

    def test_voice_change_invalidates_daily_export_reuse(self):
        product = self.product()
        output = self.root / "narrated.mp4"
        output.write_bytes(b"fixture")
        with patch.dict(os.environ, {"ELEVENLABS_VOICE_ID": "first-voice"}):
            result = {"video": str(output), "poster": str(self.root / "poster.jpg"),
                      "metadata": {"duration": 15}, "narration_settings": narration_settings(), "renderer_version": RENDERER_VERSION}
            with patch("studio.service.render_video", return_value=result):
                project = self.service.generate_daily_ad(product["id"], narration=True)
            with patch("studio.service.check_export", return_value=result["metadata"]), patch("studio.service.render_video") as renderer:
                self.service.complete_daily_ad(project["id"], narration=True)
                renderer.assert_not_called()
        with patch.dict(os.environ, {"ELEVENLABS_VOICE_ID": "second-voice"}), patch("studio.service.render_video", return_value=result) as renderer:
            self.service.complete_daily_ad(project["id"], narration=True)
            renderer.assert_called_once()

    def test_sfx_without_voice_invalidates_silent_export_and_then_reuses_audio(self):
        product = self.product()
        output = self.root / "draft.mp4"
        output.write_bytes(b"fixture")
        result = {"video": str(output), "poster": str(self.root / "poster.jpg"),
                  "metadata": {"duration": 15}, "renderer_version": RENDERER_VERSION}
        with patch("studio.service.render_video", return_value=result):
            project = self.service.generate_daily_ad(product["id"], quality="draft", narration=False)
        with patch("studio.service.render_video", return_value=result) as render:
            updated = self.service.complete_daily_ad(project["id"], quality="draft", narration=False, include_sfx=True)
            render.assert_called_once()
            self.assertTrue(render.call_args.kwargs["include_sfx"])
        self.assertTrue(updated["renders"][-1]["sfx"])
        with patch("studio.service.check_export", return_value=result["metadata"]) as check, patch("studio.service.render_video") as render:
            self.service.complete_daily_ad(project["id"], quality="draft", narration=False, include_sfx=True)
            render.assert_not_called()
            self.assertTrue(check.call_args.args[-1])

    def test_daily_lock_prevents_parallel_duplicate_reservation(self):
        p = self.product()
        with FileLock(self.root / ".campaign.lock", "busy"):
            with self.assertRaisesRegex(StudioError, "Another daily"):
                self.service.create_daily_project(p["id"])
        self.assertEqual(self.service.list_product_ads(p["id"]), [])

    def test_url_key_drops_tracking_but_not_site_identity(self):
        self.assertEqual(source_key("forma.example/?utm_source=abc"), "https://forma.example/")
        with self.assertRaises(StudioError):
            source_key("http://forma.example")
