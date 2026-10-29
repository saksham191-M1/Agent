"""Local-browser layout and seekability checks; opt in with STUDIO_RENDER_TESTS=1."""
import io
import os
import tempfile
import unittest
from pathlib import Path

from studio.render import build_document
from studio.service import StudioService


@unittest.skipUnless(os.environ.get("STUDIO_RENDER_TESTS") == "1", "Set STUDIO_RENDER_TESTS=1 for browser layout checks")
class CompositionTests(unittest.TestCase):
    def test_scene_images_switch_animate_and_reproduce_after_seeking(self):
        from playwright.sync_api import sync_playwright
        from PIL import Image
        brief = {"name": "Product", "description": "A workspace for shared projects.", "audience": "Small teams",
                 "benefits": "Keep project work together", "cta": "Explore", "duration": 20}
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            root = Path(td)
            images = []
            for index, color in enumerate(("red", "green", "blue", "gold")):
                path = root / f"scene-{index}.png"
                Image.new("RGB", (720, 620 - index * 140), color).save(path)
                images.append(str(path))
            project = StudioService(root / "projects", load_environment=False).create_project(brief, scene_image_paths=images)
            browser = pw.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 360, "height": 640})
                page.route("**/*", lambda route: route.abort())
                page.set_content(build_document(project, True))
                page.evaluate("window.ready")
                for time, scene in ((1, 0), (5, 1), (11, 2), (17, 3)):
                    page.evaluate("window.renderAt", time)
                    state = page.evaluate("""() => [...document.querySelectorAll('.scene-shot')].map(img => ({
                        opacity: Number(img.style.opacity), transform: img.style.transform, ready: img.naturalWidth > 0
                    }))""")
                    self.assertEqual([s["opacity"] for s in state], [int(i == scene) for i in range(4)])
                    self.assertTrue(all(s["ready"] for s in state))
                    self.assertTrue(page.evaluate("""() => {
                        const image=document.getElementById('product').getBoundingClientRect();
                        const caption=document.getElementById('caption').getBoundingClientRect();
                        return caption.top>=image.bottom || caption.bottom<=image.top;
                    }"""), "Captions must not cover the product image")
                    transform = state[scene]["transform"]
                    page.evaluate("window.renderAt", time + .5)
                    self.assertNotEqual(page.locator('.scene-shot').nth(scene).evaluate("e=>e.style.transform"), transform)
                    page.evaluate("window.renderAt", time)
                    self.assertEqual(page.locator('.scene-shot').nth(scene).evaluate("e=>e.style.transform"), transform)
                self.assertFalse(page.locator('#board').is_visible())
                self.assertFalse(page.locator('#tag').is_visible())
                self.assertTrue(page.locator('#caption').is_visible())
            finally:
                browser.close()

    def test_templates_are_seekable_and_keep_long_copy_in_frame(self):
        from playwright.sync_api import sync_playwright
        from PIL import Image, ImageChops, ImageStat
        brief = {"name": "Forma Product Workspace", "description": "A workspace for planning a product launch with the whole team.",
                 "problem": "Launch materials are scattered across different places.",
                 "audience": "Product teams and independent creators", "benefits": "Keep all of your launch tasks and creative feedback together in the same shared project workspace\nReview your launch materials alongside the rest of the product team\nShare a clear plan with everyone involved", "cta": "Explore the product workspace", "url": "forma.example", "duration": 15}
        with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
            root = Path(td)
            service = StudioService(root / "projects", load_environment=False)
            browser = pw.chromium.launch()
            try:
                for template in ("spotlight", "problem_solution"):
                    for aspect, size in (("9:16", (360, 640)), ("16:9", (640, 360)), ("1:1", (360, 360))):
                        with self.subTest(template=template, aspect=aspect):
                            project = service.create_project({**brief, "template": template, "aspect": aspect})
                            project["scenes"][0]["headline"] = "A beautifully organized home for every part of your next product launch"
                            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
                            page.route("**/*", lambda route: route.abort())
                            errors = []
                            page.on("pageerror", lambda e: errors.append(str(e)))
                            page.set_content(build_document(project, False))
                            page.evaluate("window.ready")
                            for time, scene in ((1, 0), (4, 1), (8, 2), (13, 3)):
                                self.assertEqual(page.evaluate("window.renderAt", time)["scene"], scene)
                                checks = page.evaluate("""() => {
                                  const h=document.getElementById('headline').getBoundingClientRect();
                                  const copy=document.getElementById('copy').getBoundingClientRect();
                                  const board=document.getElementById('board');
                                  const tag=document.getElementById('tag').getBoundingClientRect();
                                  return {headlineWithin: h.left>=copy.left-1 && h.right<=copy.right+1 && h.top>=copy.top-1 && h.bottom<=copy.bottom+1,
                                    boardFits:board.scrollHeight<=board.clientHeight+1, tagWithin:tag.right<=innerWidth+1};
                                }""")
                                self.assertTrue(checks["headlineWithin"], checks)
                                self.assertTrue(checks["boardFits"], checks)
                                self.assertTrue(checks["tagWithin"], checks)
                            page.evaluate("window.renderAt", 4)
                            first = page.screenshot()
                            page.evaluate("window.renderAt", 1)
                            page.evaluate("window.renderAt", 4)
                            delta = ImageChops.difference(Image.open(io.BytesIO(first)).convert('RGB'),
                                                          Image.open(io.BytesIO(page.screenshot())).convert('RGB'))
                            # GPU text antialiasing may differ by one level in a few pixels after a layer rebuild.
                            self.assertLess(max(ImageStat.Stat(delta).mean), .02,
                                            "Seeking to the same time must reproduce the same composition")
                            self.assertFalse(errors)
                            page.close()
                # Actual local logo/screenshot decoding, not only the no-upload path.
                image = root / "source.png"
                Image.new("RGB", (720, 480), "#6558bc").save(image)
                project = service.create_project(brief, logo_path=str(image), screenshot_path=str(image))
                page = browser.new_page(viewport={"width": 360, "height": 640})
                page.route("**/*", lambda route: route.abort())
                page.set_content(build_document(project, True))
                self.assertTrue(page.evaluate("window.ready"))
                page.evaluate("window.renderAt", 1)
                self.assertTrue(page.locator('#screenshot').is_visible())
                self.assertTrue(page.locator('#caption').is_visible())
                page.close()
            finally:
                browser.close()
