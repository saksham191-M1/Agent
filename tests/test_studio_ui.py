"""Real, local browser-to-service smoke test. Opt in: STUDIO_UI_TESTS=1.
No .env is read, no paid providers are used, and server/browser are always closed.
"""
import os
import socket
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


@unittest.skipUnless(os.environ.get("STUDIO_UI_TESTS") == "1", "Set STUDIO_UI_TESTS=1 for the real studio UI smoke test")
class StudioUITests(unittest.TestCase):
    def test_groq_fill_preserves_manual_fields_and_is_reviewable_without_saving(self):
        os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
        from playwright.sync_api import sync_playwright, expect
        from studio.service import StudioService
        from ui.studio_app import CSS, THEME, build_ui
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = StudioService(root / "projects", load_environment=False)
            app = build_ui(service)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            try:
                app.launch(server_name="127.0.0.1", server_port=port, share=False, inbrowser=False,
                           prevent_thread_lock=True, allowed_paths=[str(root)], theme=THEME, css=CSS,
                           footer_links=[], quiet=True)
                with sync_playwright() as pw:
                    browser = pw.chromium.launch()
                    try:
                        page = browser.new_page(viewport={"width": 1440, "height": 1000})
                        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(
                            (f"http://127.0.0.1:{port}/", "data:", "blob:")) else route.abort())
                        page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
                        page.get_by_role("textbox", name="Product / project name").fill("Actual Product")
                        page.get_by_role("textbox", name="Product description *").fill("A workspace for project tasks and notes.")
                        page.get_by_role("textbox", name="Who is it for? *").fill("Small teams")
                        benefits = page.get_by_role("textbox", name="Real product benefits *")
                        benefits.fill("My reviewed benefit")
                        with patch.object(service, "suggest_brief_fields", return_value={
                                "problem": "Tasks and notes are scattered.", "benefits": "AI suggestion", "model": "test-model"}) as suggest:
                            page.get_by_role("button", name="Fill problem & benefits with Groq", exact=False).click()
                            page.get_by_text("Suggestions ready — review the facts", exact=True).wait_for(timeout=30000)
                            expect(page.get_by_role("textbox", name="Customer problem")).to_have_value("Tasks and notes are scattered.")
                            expect(benefits).to_have_value("My reviewed benefit")
                            self.assertEqual(suggest.call_count, 1)
                            page.get_by_role("button", name="Fill problem & benefits with Groq", exact=False).click()
                            page.get_by_text("Your fields are already filled", exact=True).wait_for(timeout=15000)
                            self.assertEqual(suggest.call_count, 1)
                        self.assertEqual(service.list_projects(), [])
                        self.assertEqual(service.list_products(), [])
                        page.get_by_label("Replace existing problem & benefits", exact=True).check()
                        with patch.object(service, "suggest_brief_fields", side_effect=RuntimeError("secret provider error")):
                            page.get_by_role("button", name="Fill problem & benefits with Groq", exact=False).click()
                            page.get_by_text("Groq fill could not complete", exact=True).wait_for(timeout=15000)
                        expect(benefits).to_have_value("My reviewed benefit")
                        self.assertNotIn("secret provider error", page.locator('#brief-fill-status').inner_text())
                        expect(page.get_by_role("button", name="Create storyboard", exact=False)).to_be_enabled()
                    finally:
                        browser.close()
            finally:
                app.close()

    def test_create_preview_reopen_and_cancel_in_browser(self):
        os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
        from playwright.sync_api import sync_playwright, expect
        from studio.service import StudioService
        from ui.studio_app import CSS, THEME, build_ui
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = StudioService(root / "projects", load_environment=False)
            app = build_ui(service)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            try:
                app.launch(server_name="127.0.0.1", server_port=port, share=False, inbrowser=False,
                           prevent_thread_lock=True, allowed_paths=[str(root)], theme=THEME, css=CSS,
                           footer_links=[], quiet=True)
                with sync_playwright() as pw:
                    browser = pw.chromium.launch()
                    try:
                        page = browser.new_page(viewport={"width": 1440, "height": 1000})
                        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith((f"http://127.0.0.1:{port}/", "data:", "blob:")) else route.abort())
                        # Gradio keeps an SSE connection open, so networkidle is not a readiness signal.
                        page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
                        page.get_by_role("button", name="Try a fictional sample brief").click()
                        expect(page.get_by_role("textbox", name="Product / project name")).to_have_value("Forma")
                        page.get_by_role("button", name="Create storyboard", exact=False).click()
                        page.get_by_text("Storyboard ready", exact=True).wait_for(timeout=30000)
                        artifacts = os.environ.get("STUDIO_SMOKE_ARTIFACT_DIR")
                        if artifacts:
                            Path(artifacts).mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(Path(artifacts) / 'studio-desktop.png'), full_page=True)
                        self.assertEqual(len(service.list_projects()), 1)
                        project_id = service.list_projects()[0]["id"]
                        self.assertIn("fictional", service.load_project(project_id)["brief"]["description"])
                        page.locator('#storyboard-table').get_by_text('Meet Forma', exact=True).dblclick()
                        cell_editor = page.locator('#storyboard-table').get_by_role('textbox', name='Edit cell')
                        cell_editor.fill('Your next launch starts here')
                        cell_editor.press('Tab')
                        page.get_by_text('Unsaved scene edits', exact=True).wait_for(timeout=10000)
                        page.get_by_role("button", name="Render draft", exact=False).click()
                        page.get_by_text("Draft ready", exact=True).wait_for(timeout=180000)
                        project = service.load_project(project_id)
                        self.assertEqual(project["status"], "ready")
                        self.assertEqual(project['scenes'][0]['headline'], 'Your next launch starts here')
                        self.assertEqual(project['revision'], 2)
                        self.assertTrue(Path(project["draft_path"]).is_file())
                        self.assertTrue(project["renders"][-1]["metadata"]["audio"], "Default SFX must work with narration off")
                        self.assertTrue(project["renders"][-1]["sfx"])
                        self.assertFalse(project["renders"][-1]["narrated"])
                        expect(page.locator("video")).to_be_visible(timeout=20000)
                        video_url = page.locator("video").evaluate("e => e.currentSrc || e.src || e.querySelector('source')?.src")
                        self.assertTrue(video_url)
                        self.assertEqual(page.request.get(video_url).status, 200)
                        for filename in ("voiceover.txt", "captions.srt"):
                            link = page.get_by_role("row", name=filename, exact=False).get_by_role("link")
                            expect(link).to_be_visible()
                            self.assertEqual(page.request.get(link.get_attribute("href")).status, 200)
                        page.get_by_role("button", name="Open selected project", exact=True).click()
                        page.get_by_text("Draft ready", exact=True).wait_for(timeout=20000)
                        # Start an actual final render and cancel the backend, not merely its frontend event.
                        page.get_by_role("button", name="Render final", exact=False).click()
                        page.get_by_role("button", name="Cancel active render").wait_for()
                        import time
                        for _ in range(100):
                            if service.load_project(project_id)["status"] == "rendering":
                                break
                            time.sleep(.1)
                        self.assertEqual(service.load_project(project_id)["status"], "rendering")
                        page.get_by_role("button", name="Cancel active render").click()
                        page.get_by_text("Render cancelled", exact=True).wait_for(timeout=30000)
                        self.assertEqual(service.load_project(project_id)["status"], "cancelled")
                        self.assertIsNone(service.load_project(project_id)["final_path"])
                        # The shell remains usable without horizontal page overflow on a phone.
                        page.set_viewport_size({"width": 390, "height": 844})
                        page.wait_for_timeout(250)
                        overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
                        self.assertLessEqual(overflow, 4)
                        self.assertGreaterEqual(page.locator('#storyboard-table table').evaluate('e => e.clientWidth'), 770)
                        if artifacts:
                            page.screenshot(path=str(Path(artifacts) / 'studio-mobile.png'), full_page=True)
                    finally:
                        browser.close()
            finally:
                app.close()
