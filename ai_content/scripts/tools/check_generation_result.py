import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_IMG = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output\flow_generation_result.png")


def check_generation_result():
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

        logger.info("Connecting back to Google Flow studio project...")
        page.goto("https://flow.google.com/project/b1738d97-3bd8-4338-82f2-3cf537d61029", wait_until="domcontentloaded")
        page.wait_for_timeout(8000)

        OUTPUT_IMG.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(OUTPUT_IMG))
        logger.info(f"Updated status screenshot saved to: {OUTPUT_IMG}")

        browser.close()


if __name__ == "__main__":
    check_generation_result()
