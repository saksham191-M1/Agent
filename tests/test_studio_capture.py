"""Public-page capture through the real browser with an offline network fixture."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.capture import capture_public_sections
from studio.capture import capture_public_visuals
from studio.discovery import _Response
from studio.service import StudioService


@unittest.skipUnless(os.environ.get("STUDIO_RENDER_TESTS") == "1", "Set STUDIO_RENDER_TESTS=1 for static website capture")
class PublicCaptureTests(unittest.TestCase):
    def test_recorded_public_tour_has_real_page_motion_and_a_source_manifest(self):
        import subprocess
        from studio.render import probe_media
        site = "https://product.example/"
        html = b'''<html><head><title>Product</title><style>
        body{margin:0}section{height:900px;font:40px sans-serif;padding:100px}</style></head><body><main>
        <section style="background:red">Actual product home</section>
        <section style="background:green">Actual product features</section>
        <section style="background:blue">Actual workflow documentation</section>
        <section style="background:gold">Actual next step</section></main></body></html>'''
        def fetch(_self, url, *args, **kwargs):
            self.assertEqual(url, site)
            return _Response(200, {"content-type": "text/html"}, html, site)
        with tempfile.TemporaryDirectory() as td, patch("studio.capture._Fetcher.fetch", new=fetch):
            result = capture_public_visuals(site, Path(td), record_tour=True)
            self.assertIn("tour", result, result["warnings"])
            tour = result["tour"]
            self.assertEqual(tour["source"], site)
            self.assertEqual(tour["method"], "recorded public-page scrolling")
            self.assertFalse(tour["authenticated_task"])
            self.assertEqual(len(tour["actions"]), 3)
            self.assertGreater(float(probe_media(Path(tour["path"]))["format"]["duration"]), 23)
            frames = []
            for time in (1, 9, 17, 23):
                frame = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(time), "-i", tour["path"],
                                        "-frames:v", "1", "-vf", "scale=1:1", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                                       capture_output=True, check=True)
                frames.append(frame.stdout)
            self.assertEqual(len(set(frames)), 4, "A recorded tour must show actual page movement, not one static frame")

    def test_website_import_collects_real_page_shots_and_reuses_them_in_a_project(self):
        from PIL import Image
        site = "https://product.example/"
        body = b'''<html><head><title>Product</title>
        <meta property="og:site_name" content="Product">
        <meta name="description" content="A shared workspace for project tasks and notes.">
        <style>body{margin:0}section{height:900px;padding:80px;font:30px sans-serif}
        #hero{background:#d62828}#tasks{background:#208b3a}#notes{background:#2448bb}#next{background:#ffc300}</style>
        </head><body><main><section id="hero"><h1>Built for small teams</h1></section>
        <section class="features" id="tasks"><h2>Keep project work together</h2></section>
        <section class="features" id="notes"><h2>Review notes in one workspace</h2></section>
        <section id="next"><a href="/start">Get started</a></section></main>
        <script>document.body.textContent='An invented dashboard';fetch('/executed');</script></body></html>'''
        calls = []
        def fetch(_self, url, *args, **kwargs):
            calls.append(url)
            self.assertEqual(url, site)
            return _Response(200, {"content-type": "text/html"}, body, site)
        with tempfile.TemporaryDirectory() as td, patch("studio.discovery._Fetcher.fetch", new=fetch):
            service = StudioService(Path(td), load_environment=False)
            imported = service.import_product(site, capture_visuals=True)
            self.assertEqual(imported["brief"]["name"], "Product")
            self.assertEqual(imported["brief"]["audience"], "small teams")
            self.assertEqual(imported["brief"]["benefits"], ["Keep project work together", "Review notes in one workspace"])
            self.assertEqual(calls, [site], "The capture should reuse the fetched homepage")
            shots = imported["discovery"]["captures"]["captures"]
            self.assertEqual(len(shots), 4)
            for shot, color in zip(shots, ((214, 40, 40), (32, 139, 58), (36, 72, 187), (255, 195, 0))):
                self.assertEqual(shot["source"], site)
                with Image.open(shot["path"]) as image:
                    self.assertEqual(image.convert("RGB").getpixel((600, 450)), color)
            saved = service.save_product(imported["id"], imported["brief"])
            ad = service.create_daily_project(saved["id"])
            self.assertTrue(all(Path(ad["assets"][f"scene_{i}"]).is_file() for i in range(1, 5)))
            self.assertEqual(ad["creative_strategy"]["proof_method"], "product_image")

    def test_hidden_sections_are_captured_without_running_site_scripts(self):
        from PIL import Image
        site = "https://product.example/"
        html = b'''<html><head><title>Product</title><link rel="stylesheet" href="/brand.css"></head>
        <body><section class="reveal" id="proof">Public product proof</section>
        <script>document.getElementById('proof').remove();fetch('/executed');</script>
        <img src="https://third-party.example/tracker.png"></body></html>'''
        routes = {site: _Response(200, {"content-type": "text/html"}, html, site),
                  site + "brand.css": _Response(200, {"content-type": "text/css"},
                      b".reveal{opacity:0;width:600px;height:320px;background:#c99a4e}", site + "brand.css")}
        def fetch(_self, url, *args, **kwargs):
            self.assertIn(url, routes, "Capture must only fetch the public document and its allowed assets")
            return routes[url]
        with tempfile.TemporaryDirectory() as td, patch("studio.capture._Fetcher.fetch", new=fetch):
            result = capture_public_sections(site, Path(td), ["#proof"], width=800)
            self.assertEqual(result["captures"][0]["selector"], "#proof")
            self.assertTrue((Path(td) / "sources.json").is_file())
            with Image.open(result["captures"][0]["path"]) as image:
                self.assertEqual(image.size, (600, 320))
                self.assertEqual(image.convert("RGB").getpixel((300, 160)), (201, 154, 78))
