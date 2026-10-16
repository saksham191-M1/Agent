import logging
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_DIR = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output")


def trigger_approval_and_watch():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=str(STORAGE_STATE),
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        logger.info("Opening Google Flow...")
        page.goto("https://flow.google.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Open latest project
        latest_proj = page.locator("a[href*='/project/'], [data-project-id]").first
        if latest_proj.count() > 0:
            logger.info("Entering latest project...")
            latest_proj.click()
            page.wait_for_timeout(4000)

        # Find Always approve or Approve span
        always_approve = page.locator("span.option-label:has-text('Always approve'), :text('Always approve')").first
        approve = page.locator("span.option-label:has-text('Approve'), :text('Approve')").first

        target_btn = None
        if always_approve.count() > 0 and always_approve.is_visible():
            target_btn = always_approve
            logger.info("Targeting 'Always approve'...")
        elif approve.count() > 0 and approve.is_visible():
            target_btn = approve
            logger.info("Targeting 'Approve'...")

        if target_btn:
            logger.info("Clicking approval element...")
            target_btn.click()
            logger.info("Successfully clicked approval! Watching generation start...")
        else:
            logger.warning("No approval element visible right now.")

        # Watch for 25 seconds and log status
        for i in range(5):
            page.wait_for_timeout(5000)
            img_path = OUTPUT_DIR / f"generation_progress_{i+1}.png"
            page.screenshot(path=str(img_path))
            
            # Check for video elements or canvas media
            videos = page.locator("video")
            logger.info(f"[{i*5+5}s] Videos found: {videos.count()}, Screenshot: {img_path.name}")
            for v_idx in range(videos.count()):
                src = videos.nth(v_idx).get_attribute("src")
                logger.info(f"   Video {v_idx} src: {src}")

        browser.close()


if __name__ == "__main__":
    trigger_approval_and_watch()
