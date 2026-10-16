import os
import sys
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

from jarvis.ai_content.scripts.config import STORAGE_STATE_PATH, GOOGLE_FLOW_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHROME_USER_DATA = r"C:\Users\hemam\AppData\Local\Google\Chrome\User Data"


def extract_and_verify_chrome_profile(headless: bool = True):
    """
    Connects to the system's Google Chrome User Data directory,
    inheriting active Google sessions, and extracts the authenticated storage state.
    """
    logger.info("=" * 60)
    logger.info("EXTRACTING SESSION FROM CHROME USER PROFILE")
    logger.info("=" * 60)
    logger.info(f"Chrome User Data: {CHROME_USER_DATA}")
    logger.info(f"Target Output: {STORAGE_STATE_PATH}")

    STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        try:
            logger.info("Launching Chrome with Default profile...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=CHROME_USER_DATA,
                channel="chrome",
                headless=headless,
                args=[
                    "--profile-directory=Default",
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Test authentication on Google Flow / Gemini
            logger.info(f"Navigating to {GOOGLE_FLOW_URL}...")
            try:
                page.goto(GOOGLE_FLOW_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                logger.info(f"Flow page title: {page.title()} | URL: {page.url}")
            except Exception as e:
                logger.warning(f"Notice on Flow navigation: {e}")

            # Also check gemini.google.com
            logger.info("Navigating to https://gemini.google.com/ ...")
            try:
                page.goto("https://gemini.google.com/", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                logger.info(f"Gemini page title: {page.title()} | URL: {page.url}")
            except Exception as e:
                logger.warning(f"Notice on Gemini navigation: {e}")

            # Export active storage state with cookies
            context.storage_state(path=str(STORAGE_STATE_PATH))
            logger.info(f"[SUCCESS] Chrome profile session successfully exported to: {STORAGE_STATE_PATH}")

            context.close()
            return True
        except Exception as e:
            logger.error(f"Failed to extract Chrome profile: {e}")
            return False


if __name__ == "__main__":
    extract_and_verify_chrome_profile(headless=True)
