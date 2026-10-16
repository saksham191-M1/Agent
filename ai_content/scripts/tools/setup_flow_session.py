import sys
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure root paths are in sys.path regardless of where script is invoked
_CURRENT_DIR = Path(__file__).resolve().parent
_JARVIS_DIR = _CURRENT_DIR.parent.parent.parent
_ROOT_DIR = _JARVIS_DIR.parent
for p in [str(_ROOT_DIR), str(_JARVIS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

STORAGE_STATE_PATH = _CURRENT_DIR.parent.parent / "storage_state.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def capture_edge_flow_session(output_path: Path = STORAGE_STATE_PATH):
    """
    Launches Microsoft Edge (native browser) so the user can complete 1-click Google Sign-in.
    Automatically captures all cookies from flow.google.com and saves to storage_state.json.
    """
    logger.info("=" * 60)
    logger.info("GOOGLE FLOW 1-CLICK EDGE LOGIN BOOTSTRAPPER")
    logger.info("=" * 60)
    logger.info(f"Target Output: {output_path}")
    logger.info("Opening Microsoft Edge window...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        )
        page = context.new_page()

        logger.info("Navigating to https://flow.google.com/ ...")
        page.goto("https://flow.google.com/", wait_until="domcontentloaded")

        logger.info("\n>>> EDGE BROWSER OPENED! <<<")
        logger.info("1. Click 'Sign In' or click your Google profile.")
        logger.info("2. Once you reach the Google Flow dashboard (+ New project screen),")
        logger.info("   this script will automatically detect it and save your session!")
        logger.info("=" * 60)

        # Loop and auto-detect when user is on the logged in dashboard
        captured = False
        for i in range(120): # Up to 10 minutes
            time.sleep(3)
            current_url = page.url
            cookies = context.cookies()

            # Check if logged in: on flow.google.com and has flow auth cookies
            has_flow_cookies = any(c.get("domain") in [".flow.google.com", "flow.google.com", ".google.com"] and "SID" in c.get("name") for c in cookies)
            is_on_dashboard = "accounts.google.com" not in current_url and ("flow.google.com" in current_url or "labs.google" in current_url)

            if has_flow_cookies and is_on_dashboard:
                # Extra check: not on /about
                if "/about" not in current_url or any("Create" in page.content() for _ in [1]):
                    context.storage_state(path=str(output_path))
                    captured = True
                    logger.info(f"\n[SUCCESS!] Authenticated session captured: URL={current_url}")
                    logger.info(f"Saved {len(cookies)} cookies to: {output_path}")
                    break

            if page.is_closed():
                break

        if captured:
            logger.info("Session verified and ready for live Veo 3.1 generation!")
        else:
            context.storage_state(path=str(output_path))
            logger.info(f"State saved to {output_path}")

        try:
            browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    capture_edge_flow_session()
