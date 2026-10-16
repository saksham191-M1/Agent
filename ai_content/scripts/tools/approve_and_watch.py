import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_IMG = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output\flow_generating_status.png")


def approve_and_watch():
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

        # Find and click 'Always approve' or 'Approve'
        approve_btn = page.locator("button:has-text('Always approve'), [role='button']:has-text('Always approve')").first
        if approve_btn.count() == 0 or not approve_btn.is_visible():
            approve_btn = page.locator("button:has-text('Approve'), [role='button']:has-text('Approve')").first

        if approve_btn.count() > 0 and approve_btn.is_visible():
            logger.info("Clicking approval button...")
            approve_btn.click()
            page.wait_for_timeout(10000)
        else:
            logger.info("No approval button found, checking current state...")

        # Take screenshot of current state
        OUTPUT_IMG.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(OUTPUT_IMG))
        logger.info(f"Screenshot saved to: {OUTPUT_IMG}")

        # Check for videos or generation indicators
        videos = page.locator("video")
        logger.info(f"Video elements found: {videos.count()}")
        for i in range(videos.count()):
            src = videos.nth(i).get_attribute("src")
            logger.info(f"Video {i} src: {src}")

        browser.close()


if __name__ == "__main__":
    approve_and_watch()
