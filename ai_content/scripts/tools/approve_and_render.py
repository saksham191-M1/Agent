import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_IMG = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output\flow_approved_rendering.png")


def approve_latest():
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

        # Click the most recent project card
        logger.info("Opening most recent project...")
        latest_project = page.locator("a[href*='/project/'], [data-project-id]").first
        if latest_project.count() > 0:
            latest_project.click()
            page.wait_for_timeout(5000)

        # Look for 'Always approve' or 'Approve' button
        approve_btn = page.locator("text='Always approve', text='Approve'").first
        if approve_btn.count() > 0 and approve_btn.is_visible():
            logger.info("Found Credit Approval prompt! Clicking 'Always approve'...")
            approve_btn.click()
            page.wait_for_timeout(6000)
            logger.info("[SUCCESS] Clicked 'Always approve'!")
        else:
            logger.info("No approval prompt visible right now.")

        OUTPUT_IMG.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(OUTPUT_IMG))
        logger.info(f"Screenshot saved to: {OUTPUT_IMG}")

        browser.close()


if __name__ == "__main__":
    approve_latest()
